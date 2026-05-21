import os
import json
import webbrowser

class DashboardModule:
    def __init__(self, model_name="gemma4:31b-cloud"):
        # model_name kept for backward compatibility; dashboard renders deterministically now.
        self.model_name = model_name
        self.base_template_path = "interface/base.html"
        self.output_file = "interface/dashboard.html"

    def _read_base_template(self):
        try:
            with open(self.base_template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print("❌ Error: base.html not found. Please ensure it exists in the interface folder.")
            return None

    def _escape(self, value):
        if value is None:
            return ""
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _render_kpi_card(self, label, value):
        return (
            "<div class='glass-premium p-6 rounded-2xl border border-slate-800 shadow-xl'>"
            f"<p class='text-xs text-slate-500 uppercase tracking-wider mb-2'>{self._escape(label)}</p>"
            f"<p class='text-2xl font-medium text-white'>{self._escape(value) if value not in (None, '') else 'N/A'}</p>"
            "</div>"
        )

    def _render_dashboard_body(self, payload: dict) -> str:
        kpis = payload.get("kpis") or {}
        plots = payload.get("plots") or []
        research = payload.get("research") or []
        plot_explanations = payload.get("plot_explanations") or []

        temperature = kpis.get("temperature_c")
        humidity = kpis.get("humidity_percent")
        soil = kpis.get("soil_moisture")
        status = kpis.get("agent_status")

        visual_html = ""
        if plots:
            cards = []
            for p in plots:
                img_src = p.get("image") or p.get("file_path") or ""
                title = p.get("title") or os.path.basename(img_src) or "Plot"
                if img_src:
                    cards.append(
                        "<div class='glass-premium p-4 rounded-2xl border border-slate-800 shadow-xl space-y-3'>"
                        f"<p class='text-xs text-slate-400 uppercase tracking-wider'>{self._escape(title)}</p>"
                        f"<img src='{self._escape(img_src)}' class='rounded-xl border border-slate-700 w-full h-auto shadow-lg' alt='{self._escape(title)}' />"
                        "</div>"
                    )
            if cards:
                visual_html = "<div class='grid grid-cols-1 md:grid-cols-3 gap-4'>" + "".join(cards) + "</div>"

        if not visual_html:
            visual_html = (
                "<div class='grid grid-cols-1 md:grid-cols-3 gap-4'>"
                "<div class='col-span-full py-12 text-center border border-dashed border-slate-800 rounded-xl text-slate-600 italic'>"
                "No visual data streams available."
                "</div></div>"
            )

        research_cards = ""
        combined_research = list(research)
        for pe in plot_explanations:
            combined_research.append({
                "title": f"Plot Insight: {os.path.basename(pe.get('file_path','plot'))}",
                "explain": pe.get("explanation", ""),
                "link": pe.get("file_path", ""),
            })

        if combined_research:
            cards = []
            for item in combined_research[:9]:
                title = item.get("title") or "Insight"
                body = item.get("explain") or item.get("content") or ""
                link = item.get("link")
                link_html = ""
                if link:
                    link_html = f"<a class='text-xs text-cyan-300 hover:text-cyan-200' href='{self._escape(link)}' target='_blank' rel='noreferrer'>Open</a>"

                cards.append(
                    "<div class='glass-premium p-6 rounded-2xl border border-slate-800 shadow-xl space-y-3'>"
                    f"<div class='flex items-center justify-between gap-3'><p class='text-sm font-semibold text-white'>{self._escape(title)}</p>{link_html}</div>"
                    f"<p class='text-sm text-slate-300 leading-relaxed'>{self._escape(body)}</p>"
                    "</div>"
                )
            research_cards = "<div class='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>" + "".join(cards) + "</div>"
        else:
            research_cards = (
                "<div class='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>"
                "<div class='col-span-full py-12 text-center border border-dashed border-slate-800 rounded-xl text-slate-600 italic'>"
                "No research insights mapped."
                "</div></div>"
            )

        return (
            "<div class='min-h-screen p-6 space-y-6 font-sans text-slate-200 bg-slate-950'>"
            "<div class='flex justify-between items-center mb-8'>"
            "<h1 class='text-2xl font-light tracking-widest uppercase text-slate-400'>Waste-Dispo <span class='text-white font-semibold'>Intelligence Command</span></h1>"
            "<button onclick='window.close()' class='px-4 py-2 text-xs uppercase tracking-tighter bg-slate-800 hover:bg-red-900/40 border border-slate-700 transition-all duration-300 rounded-md text-slate-300'>Close Dashboard</button>"
            "</div>"
            "<div class='grid grid-cols-1 md:grid-cols-4 gap-4'>"
            f"{self._render_kpi_card('Temperature', f'{temperature}°C' if temperature is not None else None)}"
            f"{self._render_kpi_card('Humidity', f'{humidity}%' if humidity is not None else None)}"
            f"{self._render_kpi_card('Soil Moisture', soil)}"
            f"{self._render_kpi_card('Agent Status', status)}"
            "</div>"
            "<div class='space-y-4'>"
            "<h2 class='text-sm uppercase tracking-widest text-slate-500 font-semibold'>Visual Analytics</h2>"
            f"{visual_html}"
            "</div>"
            "<div class='space-y-4'>"
            "<h2 class='text-sm uppercase tracking-widest text-slate-500 font-semibold'>Research Intelligence</h2>"
            f"{research_cards}"
            "</div>"
            "</div>"
        )

    def generate_dashboard(self, data_json):
        """Transforms agent data into a high-end HTML dashboard (deterministic, no LLM)."""
        print("🎨 Orchestrating real-time data into luxury dashboard...")

        payload = data_json
        if isinstance(data_json, list):
            payload = {"items": data_json}

        if not isinstance(payload, dict):
            payload = {"items": [str(payload)]}

        html_content = self._render_dashboard_body(payload)

        base_html = self._read_base_template()
        if not base_html:
            return False

        final_html = base_html.replace("{{CONTENT}}", html_content).replace("{{DASHBOARD_BODY}}", html_content)

        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(final_html)
            return True
        except Exception as e:
            print(f"Error generating dashboard: {e}")
            return False

    def open_dashboard(self):
        """Opens the generated dashboard in a new window."""
        path = os.path.abspath(self.output_file)
        webbrowser.open_new(f"file://{path}")
        print(f"🚀 Dashboard opened: {path}")

    def close_dashboard(self):
        print("ℹ️ Please use the 'Close Dashboard' button within the browser window.")
