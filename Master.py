import json
import ollama
import re
import os
import shutil
import time
from typing import List, Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Importing your agents
from Agents.env_live import EnvironmentalDataFetcher
from image.explain import Vision 
from Agents.Plotter import AIPlotterApp
from Agents.research import ResearchAnalyzer
from display.Dashboard import DashboardModule

class SessionManager:
    """Handles temporary data storage and session cleanup."""
    def __init__(self, filename="session_state.json"):
        self.filename = filename

    def save(self, data):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def cleanup(self):
        print("\n🧹 Cleaning up session data...")
        # Keep session_state.json so cached data can be reused (e.g., 1-hour env cache).
        print("✅ Session closed.")

class WasteDispoMaster:
    ENV_CACHE_TTL_SECONDS = 60 * 60  # 1 hour

    def __init__(self, model_name="gemma4:31b-cloud", lite_model="gemma2:2b", default_location="Chittarikkal, Kerala, India"):
        self.model_name = model_name
        self.lite_model = lite_model
        self.session = SessionManager()
        
        # Initialize context from saved session or defaults
        saved_data = self.session.load()
        self.context = {
            "location": saved_data.get("location", default_location),
            "knowledge_base": saved_data.get("knowledge_base", {}),
            "is_processing": False,
            "created_files": saved_data.get("created_files", [])
        }
        
        self.agents = {
            "env_agent": {"module": EnvAgentWrapper(), "description": "Real-time weather, soil, and env data.", "type": "DATA"},
            "vision_agent": {"module": VisionAgentWrapper(), "description": "Analyzes images of waste.", "type": "TEXT"},
            "plotter_agent": {"module": PlotterAgentWrapper(), "description": "Creates high-end data visualizations.", "type": "FILE"},
            "search_agent": {"module": ResearchAgentWrapper(), "description": "Deep internet research on waste/chemicals.", "type": "REPORT"},
            "classifier_agent": {"module": None, "description": "Classifies waste (Under Construction)", "type": "TEXT"},
            "dashboard_agent": {"module": DashboardAgentWrapper(), "description": "Generates a comprehensive Intelligence Command Center.", "type": "FILE"}
        }

    def _get_system_prompt(self):
        agent_desc = "\n".join([f"- {name}: {info['description']}" for name, info in self.agents.items()])
        return (
            f"You are the 'Waste-Dispo Master', a high-end Environmental Intelligence Orchestrator. "
            f"Your goal is to provide a seamless, luxury-grade experience. \n\n"
            f"--- 🛑 STRICT NICHE GUARDRAIL ---\n"
            f"REFUSE all non-environmental queries. Only discuss waste, pollution, soil, and sustainability.\n\n"
            f"--- ⚙️ OPERATIONAL MODE ---\n"
            f"Default to CHATTING and reasoning first. Only trigger agents when the user explicitly asks for: "
            f"live environmental measurements, web research, a plot/image generation, image analysis, or the dashboard.\n"
            f"Avoid running multiple agents per turn unless the user requests a full report.\n"
            f"IMPORTANT: Reuse cached environmental data for 1 hour when available; do not re-fetch unnecessarily.\n\n"
            f"--- CONTEXT ---\n"
            f"Current User Location: {self.context['location']}\n\n"
            f"AVAILABLE TOOLS:\n{agent_desc}\n\n"
            f"OUTPUT FORMAT:\n"
            f"Return a JSON list of actions: [ {{ 'intent': 'agent_name', 'parameters': {{ 'key': 'value' }} }} ]\n"
            f"If just chatting, respond as a world-class expert."
        )

    def _now(self) -> int:
        return int(time.time())

    def _get_cache(self) -> Dict:
        kb = self.context.setdefault("knowledge_base", {})
        return kb.setdefault("_cache", {})

    def _get_cached_env(self, place: str):
        cache = self._get_cache()
        env_cache = cache.get("env")
        if not env_cache:
            return None

        if (env_cache.get("place") or "").strip().lower() != (place or "").strip().lower():
            return None

        fetched_at = env_cache.get("fetched_at")
        if not isinstance(fetched_at, int):
            return None

        if self._now() - fetched_at > self.ENV_CACHE_TTL_SECONDS:
            return None

        return env_cache.get("result")

    def _set_cached_env(self, place: str, result: Dict):
        cache = self._get_cache()
        cache["env"] = {
            "place": place,
            "fetched_at": self._now(),
            "ttl_seconds": self.ENV_CACHE_TTL_SECONDS,
            "result": result,
        }

    def _should_explain_plots(self, user_text: str) -> bool:
        if not user_text:
            return False
        text = user_text.lower()
        return any(k in text for k in ["explain", "insight", "analyze", "analyse", "interpret", "what does this plot", "what does this chart"]) 

    def _is_full_report_request(self, user_text: str) -> bool:
        if not user_text:
            return False
        text = user_text.lower()
        return any(k in text for k in ["full report", "full data report", "detailed report", "detailed analysis", "full analysis"]) 

    def _cleanup_previous_outputs(self):
        """Deletes only files previously generated by agents (tracked in created_files)."""
        created = self.context.get("created_files") or []
        if not isinstance(created, list) or not created:
            created = []

        kept = []
        for path in created:
            try:
                if path and os.path.exists(path) and os.path.isfile(path):
                    os.remove(path)
                else:
                    kept.append(path)
            except Exception:
                kept.append(path)

        # Reset to what couldn't be deleted
        self.context["created_files"] = kept

        # Also clear old generated visuals/dashboard so each report is clean.
        try:
            if os.path.exists("interface/dashboard.html"):
                os.remove("interface/dashboard.html")
        except Exception:
            pass

        try:
            if os.path.isdir("display"):
                for name in os.listdir("display"):
                    if name.lower().endswith(".png"):
                        try:
                            os.remove(os.path.join("display", name))
                        except Exception:
                            pass
        except Exception:
            pass

    def _plot_env_snapshot_fallback(self, env_res: Dict) -> Dict:
        """Deterministic fallback plot from current env metrics."""
        try:
            env_data = (env_res or {}).get("environmental_data", {})
            place = (env_res or {}).get("place") or self.context.get("location") or "Unknown"
            metrics = {
                "Temp (°C)": env_data.get("temperature"),
                "Humidity (%)": env_data.get("humidity"),
                "Wind": env_data.get("wind_speed") or env_data.get("windspeed_openmeteo"),
                "Soil": env_data.get("soil_moisture_0_to_7cm") or env_data.get("soil_moisture_7_to_28cm"),
            }

            labels = [k for k, v in metrics.items() if v is not None]
            values = [float(metrics[k]) for k in labels]
            if not labels:
                return {"success": False, "error": "No numeric env metrics available to plot."}

            os.makedirs("display", exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join("display", f"env_snapshot_{ts}.png")

            plt.figure(figsize=(10, 5))
            plt.bar(labels, values)
            plt.title(f"Environmental Snapshot — {place}")
            plt.ylabel("Value")
            plt.xticks(rotation=15, ha="right")
            plt.tight_layout()
            plt.savefig(file_path, dpi=200, bbox_inches="tight")
            plt.close()

            return {"success": True, "file_path": file_path, "source": "fallback"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_full_report_pipeline(self, user_text: str) -> str:
        self.context["is_processing"] = True
        execution_log = []

        # Clear prior generated outputs so the dashboard reflects only this run.
        self._cleanup_previous_outputs()

        # 1) ENV (cached)
        place = self.context.get("location") or "Unknown"
        cached = self._get_cached_env(place)
        if cached:
            env_res = {"success": True, "cached": True, **cached}
        else:
            env_res = self.agents["env_agent"]["module"].run({"place": place})
            if isinstance(env_res, dict) and env_res.get("success"):
                self._set_cached_env(place, env_res)
        self.context["knowledge_base"]["env_agent"] = env_res
        execution_log.append({"agent": "env_agent", "result": env_res})

        # 2) RESEARCH
        research_query = f"Waste management, pollution, and sustainability updates for {place}".strip()
        search_res = self.agents["search_agent"]["module"].run({"query": research_query})
        self.context["knowledge_base"]["search_agent"] = search_res
        execution_log.append({"agent": "search_agent", "result": search_res})

        # 3) PLOT (deterministic: reduce agent work + avoid LLM plot failures)
        plot_res = self._plot_env_snapshot_fallback(env_res if isinstance(env_res, dict) else {})

        self.context["knowledge_base"]["plotter_agent"] = plot_res
        execution_log.append({"agent": "plotter_agent", "result": plot_res})

        if isinstance(plot_res, dict) and plot_res.get("file_path") and plot_res.get("file_path") not in self.context["created_files"]:
            self.context["created_files"].append(plot_res.get("file_path"))

        # Optional: explain the plot using vision when the user asks for insights/explanation.
        if self._should_explain_plots(user_text) and isinstance(plot_res, dict) and plot_res.get("success") and plot_res.get("file_path"):
            vision_params = {
                "image_path": plot_res.get("file_path"),
                "prompt": (
                    "Explain this chart in detail. Identify axes, key trends, and what it implies about waste/environment. "
                    "Provide 3-5 concise insights and 1-2 recommended actions."
                ),
            }
            vision_text = self.agents["vision_agent"]["module"].run(vision_params)
            self.context.setdefault("knowledge_base", {}).setdefault("plot_explanations", []).append({
                "file_path": plot_res.get("file_path"),
                "explanation": vision_text,
            })
            execution_log.append({"agent": "vision_agent", "result": {"success": True, "file_path": plot_res.get("file_path"), "explanation": vision_text}})

        # 4) DASHBOARD
        dash_res = self.agents["dashboard_agent"]["module"].run({"knowledge_base": self.context["knowledge_base"]})
        self.context["knowledge_base"]["dashboard_agent"] = dash_res
        execution_log.append({"agent": "dashboard_agent", "result": dash_res})
        if isinstance(dash_res, dict) and dash_res.get("file_path") and dash_res.get("file_path") not in self.context["created_files"]:
            self.context["created_files"].append(dash_res.get("file_path"))

        self.context["is_processing"] = False
        self.session.save(self.context)

        # Deterministic response (avoid an extra synthesis LLM call that can hang).
        env_data = (env_res or {}).get("environmental_data", {}) if isinstance(env_res, dict) else {}
        temperature = env_data.get("temperature")
        humidity = env_data.get("humidity")
        soil = env_data.get("soil_moisture_0_to_7cm") or env_data.get("soil_moisture_7_to_28cm")
        cached_flag = " (cached)" if isinstance(env_res, dict) and env_res.get("cached") else ""

        report_titles = []
        if isinstance(search_res, dict) and search_res.get("success"):
            for item in (search_res.get("report") or [])[:3]:
                t = (item or {}).get("title")
                if t:
                    report_titles.append(t)

        dash_path = None
        if isinstance(dash_res, dict):
            dash_path = dash_res.get("file_path")

        plot_path = plot_res.get("file_path") if isinstance(plot_res, dict) else None

        lines = [
            f"Environmental snapshot for {place}{cached_flag}:",
            f"- Temperature: {temperature if temperature is not None else 'N/A'} °C",
            f"- Humidity: {humidity if humidity is not None else 'N/A'} %",
            f"- Soil moisture: {soil if soil is not None else 'N/A'}",
        ]
        if report_titles:
            lines.append("Top research signals:")
            for t in report_titles:
                lines.append(f"- {t}")
        if plot_path:
            lines.append(f"Plot saved: {plot_path}")
        if dash_path:
            lines.append(f"Dashboard: {dash_path}")

        return "\n".join(lines)

    def _should_run_plotter(self, params: Dict, user_text: str) -> bool:
        # For full reports, allow plotting even if the user didn't provide explicit data.
        if self._is_full_report_request(user_text):
            return True
        query = (params or {}).get("query")
        if query and isinstance(query, str) and query.strip():
            return True
        # Only run plotter if user explicitly asked for a plot/chart and provided data.
        if not user_text:
            return False
        text = user_text.lower()
        asked = any(k in text for k in ["plot", "chart", "graph", "visualize", "visualise"])
        has_numbers = any(ch.isdigit() for ch in text)
        return asked and has_numbers

    def process_input(self, user_text):
        if self._is_full_report_request(user_text):
            return self._run_full_report_pipeline(user_text)

        # 1. Decide Intent
        # Use the lighter model for intent/planning when available.
        decision_model = self.lite_model or self.model_name
        try:
            response = ollama.chat(
                model=decision_model,
                messages=[{'role': 'system', 'content': self._get_system_prompt()}, {'role': 'user', 'content': user_text}]
            )
        except Exception:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'system', 'content': self._get_system_prompt()}, {'role': 'user', 'content': user_text}]
            )
        ai_content = response['message']['content']

        if "[" in ai_content and "intent" in ai_content:
            try:
                json_str = re.search(r"\[.*\]", ai_content, re.DOTALL).group()
                actions = json.loads(json_str)

                # If user is requesting a full dashboard/report, clear previous generated outputs
                # so the new run doesn't mix old plots/cards.
                if self._is_full_report_request(user_text) or any(a.get("intent") == "dashboard_agent" for a in (actions or [])):
                    self._cleanup_previous_outputs()

                # Reduce agent workload unless a full report is explicitly requested.
                if isinstance(actions, list) and not self._is_full_report_request(user_text):
                    actions = actions[:1]
                
                # Start background processing
                self.context["is_processing"] = True
                execution_log = []

                # Defer dashboard until the end so it receives the updated knowledge base.
                dashboard_requested = any(a.get("intent") == "dashboard_agent" for a in actions)
                actions = [a for a in actions if a.get("intent") != "dashboard_agent"]

                # Run core data agents first for better downstream prompts.
                priority = {"env_agent": 0, "search_agent": 1, "plotter_agent": 2, "vision_agent": 3}
                try:
                    actions.sort(key=lambda a: priority.get(a.get("intent"), 99))
                except Exception:
                    pass
                
                for action in actions:
                    intent = action.get("intent")
                    params = action.get("parameters", {})

                    if intent in self.agents and self.agents[intent]["module"]:
                        # ENV caching: reuse env data for 1 hour.
                        if intent == "env_agent":
                            place = params.get("place") or self.context.get("location") or "Unknown"
                            cached = self._get_cached_env(place)
                            if cached:
                                res = {"success": True, "cached": True, **cached}
                            else:
                                res = self.agents[intent]["module"].run({"place": place})
                                if isinstance(res, dict) and res.get("success"):
                                    self._set_cached_env(place, res)

                            execution_log.append({"agent": intent, "result": res})

                        else:
                            if intent == "plotter_agent" and not self._should_run_plotter(params, user_text):
                                res = {
                                    "success": False,
                                    "error": "Plotter skipped: provide a plot request with actual data points (e.g. '2010=40, 2020=55').",
                                }
                            else:
                                if intent == "plotter_agent" and (not params.get("query")):
                                    # Auto-build a sensible plot request for full reports.
                                    env_res = self.context.get("knowledge_base", {}).get("env_agent", {})
                                    env_data = env_res.get("environmental_data", {}) if isinstance(env_res, dict) else {}
                                    temperature = env_data.get("temperature")
                                    humidity = env_data.get("humidity")
                                    wind = env_data.get("wind_speed") or env_data.get("windspeed_openmeteo")
                                    soil = env_data.get("soil_moisture_0_to_7cm") or env_data.get("soil_moisture_7_to_28cm")

                                    if any(v is not None for v in [temperature, humidity, wind, soil]):
                                        place = (env_res.get("place") if isinstance(env_res, dict) else None) or self.context.get("location")
                                        auto_query = (
                                            "Create a bar chart for current environmental snapshot (one bar per metric): "
                                            f"temperature_c={temperature}, humidity_percent={humidity}, wind_speed={wind}, soil_moisture={soil}. "
                                            f"Title the plot with the place: {place}."
                                        )
                                        params = {**params, "query": auto_query}
                                    else:
                                        params = {**params, "query": user_text}
                                res = self.agents[intent]["module"].run(params)
                            execution_log.append({"agent": intent, "result": res})

                        # Track created files
                        if isinstance(res, dict):
                            file_path = res.get("file_path") or res.get("saved_to")
                            if file_path and file_path not in self.context["created_files"]:
                                self.context["created_files"].append(file_path)

                            # Optional: explain generated plots using the vision agent
                            if intent == "plotter_agent" and res.get("success") and res.get("file_path") and self._should_explain_plots(user_text):
                                vision_params = {
                                    "image_path": res.get("file_path"),
                                    "prompt": (
                                        "Explain this chart in detail. Identify the axes, key trends, outliers, and what it implies. "
                                        "Provide 3-5 concise insights and 1-2 recommended actions related to waste/environment."
                                    ),
                                }
                                vision_res = self.agents["vision_agent"]["module"].run(vision_params)
                                self.context.setdefault("knowledge_base", {}).setdefault("plot_explanations", []).append({
                                    "file_path": res.get("file_path"),
                                    "explanation": vision_res,
                                })
                                execution_log.append({"agent": "vision_agent", "result": {"success": True, "file_path": res.get("file_path"), "explanation": vision_res}})
                        
                        # Update Knowledge Base
                        self.context["knowledge_base"][intent] = res
                        if "place" in params: self.context["location"] = params["place"]

                # Run dashboard last if requested
                if dashboard_requested and self.agents["dashboard_agent"]["module"]:
                    dash_res = self.agents["dashboard_agent"]["module"].run({"knowledge_base": self.context["knowledge_base"]})
                    execution_log.append({"agent": "dashboard_agent", "result": dash_res})
                    self.context["knowledge_base"]["dashboard_agent"] = dash_res
                    if isinstance(dash_res, dict) and dash_res.get("file_path") and dash_res.get("file_path") not in self.context["created_files"]:
                        self.context["created_files"].append(dash_res.get("file_path"))

                self.context["is_processing"] = False
                self.session.save(self.context) # Save to temporary JSON
                return self._synthesize_final_response(execution_log, user_text)
            except Exception as e:
                print(f"⚙️ Orchestration Error: {e}")
                return ai_content
        
        return ai_content

    def _synthesize_final_response(self, logs, original_query):
        data_summary = json.dumps(logs, indent=2)
        prompt = (
            f"The user asked: '{original_query}'\nResults: {data_summary}\n\n"
            f"Synthesize this into a high-end expert response. Be assertive. "
            f"Inform the user that a full suite of visual analytics and the Command Center Dashboard are ready."
        )
        response = ollama.chat(model=self.model_name, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']

    def get_status_update(self):
        """The Chat-Lite Model: provides quick status updates while Master is working."""
        if not self.context["is_processing"]:
            return "The system is currently idle and ready for your next command."
        
        return "The Master AI is currently orchestrating multiple agents, synthesizing global research, and rendering your visual la- l. Please hold on a moment; perfection takes time."

# ------------------------------------------------------------------
# WRAPPERS
# ------------------------------------------------------------------
class EnvAgentWrapper:
    def __init__(self): from Agents.env_live import EnvironmentalDataFetcher; self.f = EnvironmentalDataFetcher()
    def run(self, p): return self.f.fetch_data(p.get("place", "Unknown"))

class VisionAgentWrapper:
    def __init__(self): from image.explain import Vision; self.a = Vision()
    def run(self, p): return self.a.explain_image(p.get("image_path", ""), prompt=p.get("prompt"))

class PlotterAgentWrapper:
    def __init__(self): from Agents.Plotter import AIPlotterApp; self.p = AIPlotterApp()
    def run(self, p): return self.p.generate_plot(p.get("query", ""))

class ResearchAgentWrapper:
    def __init__(self): from Agents.research import ResearchAnalyzer; self.r = ResearchAnalyzer()
    def run(self, p): return self.r.run_research(p.get("query", ""))

class DashboardAgentWrapper:
    def __init__(self): from display.Dashboard import DashboardModule; self.d = DashboardModule()
    def run(self, p):
        kb = p.get("knowledge_base", {})
        payload = {
            "kpis": {},
            "plots": [],
            "research": [],
            "plot_explanations": [],
        }
        
        # Env Card
        if "env_agent" in kb:
            env_res = kb["env_agent"] if isinstance(kb["env_agent"], dict) else {}
            env_data = env_res.get("environmental_data", {}) if env_res.get("success") else {}
            temp = env_data.get("temperature")
            humidity = env_data.get("humidity")
            soil_moisture = env_data.get("soil_moisture_0_to_7cm") or env_data.get("soil_moisture_7_to_28cm")
            payload["kpis"] = {
                "temperature_c": temp,
                "humidity_percent": humidity,
                "soil_moisture": soil_moisture,
                "agent_status": "OK" if env_res.get("success") else "N/A",
                "place": env_res.get("place"),
                "cached": env_res.get("cached", False),
            }

        # Research Cards
        if "search_agent" in kb:
            for item in kb["search_agent"].get("report", [])[:3]:
                payload["research"].append({"title": item.get('title'), "explain": item.get('explain'), "link": item.get('link')})

        # Plot explanations (optional)
        if "plot_explanations" in kb and isinstance(kb["plot_explanations"], list):
            payload["plot_explanations"] = kb["plot_explanations"][-3:]

        # Plots Gallery
        if "plotter_agent" in kb:
            # We find all .png files in the display folder to add them as links/images
            plots = [f for f in os.listdir("display") if f.endswith(".png")]
            for plot in plots:
                rel = f"../display/{plot}"
                payload["plots"].append({"title": f"Analysis Plot: {plot}", "image": rel, "file_path": rel})

        if self.d.generate_dashboard(payload):
            self.d.open_dashboard()
            return {"success": True, "file_path": self.d.output_file}
        return {"success": False}

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    MY_HOME_LOCATION = "Chittarikkal, Kerala, India"
    master = WasteDispoMaster(default_location=MY_HOME_LOCATION)
    
    print("Waste-Dispo Master AI is Online. (GOD MODE: ACTIVE)")
    
    try:
        while True:
            user_in = input("\nYou: ")
            if user_in.lower() == 'exit': break
            
            # Handle status queries via the "Lite" path
            if any(word in user_in.lower() for word in ["status", "processing", "working", "update"]):
                print(f"\nMaster (Lite): {master.get_status_update()}")
            else:
                # Normal autonomous flow
                print(f"\nMaster: {master.process_input(user_in)}")
    finally:
        master.session.cleanup()
