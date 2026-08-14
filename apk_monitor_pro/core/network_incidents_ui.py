"""
NetworkIncidentsUI - Componente de UI para exibir incidentes de rede
Integra com o logcat tool existente (it.overit.amplawfm)
Adiciona aba "Incidentes" com análise automática de causa raiz
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading
from datetime import datetime
from typing import List, Optional, Callable
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from network_incident_detector import NetworkIncidentDetector, NetworkIncident, ErrorCategory


# ---------------------------------------------------------------------------
# Paleta de cores (escuro — igual ao logcat tool existente)
# ---------------------------------------------------------------------------

COLORS = {
    "bg":           "#1e1e1e",
    "bg_secondary": "#252526",
    "bg_card":      "#2d2d30",
    "bg_hover":     "#37373d",
    "border":       "#3c3c3c",
    "text":         "#cccccc",
    "text_dim":     "#888888",
    "text_bright":  "#ffffff",
    "accent":       "#0e7fd4",
    "danger":       "#f44747",
    "warning":      "#ff8c00",
    "success":      "#4ec9b0",
    "info":         "#9cdcfe",
    # categorias
    "ssl":          "#f44747",
    "timeout":      "#ff8c00",
    "dns":          "#dcdcaa",
    "connection":   "#ce9178",
    "http":         "#4fc1ff",
    "certificate":  "#c586c0",
    "cleartext":    "#f44747",
    "socket":       "#ff8c00",
    "unknown":      "#888888",
}

CATEGORY_COLORS = {
    "SSL/TLS":               COLORS["ssl"],
    "Timeout":               COLORS["timeout"],
    "DNS":                   COLORS["dns"],
    "Conexão":               COLORS["connection"],
    "HTTP":                  COLORS["http"],
    "Certificado":           COLORS["certificate"],
    "Tráfego HTTP bloqueado":COLORS["cleartext"],
    "Socket":                COLORS["socket"],
    "Desconhecido":          COLORS["unknown"],
}


class IncidentCard(tk.Frame):
    """Card expandível para um único incidente de rede."""

    def __init__(self, parent, incident: NetworkIncident, index: int, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)
        self.incident  = incident
        self.expanded  = False
        self._build(index)

    def _build(self, index: int):
        cat_color = CATEGORY_COLORS.get(self.incident.category.value, COLORS["text_dim"])
        ts = self.incident.timestamp.strftime("%H:%M:%S.%f")[:-3]

        # ── Header ──────────────────────────────────────────────────────
        header = tk.Frame(self, bg=COLORS["bg_card"], cursor="hand2")
        header.pack(fill="x", padx=1, pady=1)

        # Número do incidente
        tk.Label(
            header, text=f"#{index+1:02d}",
            font=("Consolas", 10), bg=COLORS["bg_card"],
            fg=COLORS["text_dim"], width=4, anchor="w"
        ).pack(side="left", padx=(10, 4), pady=8)

        # Badge categoria
        badge = tk.Label(
            header, text=f" {self.incident.category.value} ",
            font=("Consolas", 9, "bold"), bg=cat_color,
            fg=COLORS["bg"], padx=4, pady=2,
            relief="flat"
        )
        badge.pack(side="left", padx=(0, 8), pady=8)

        # Timestamp
        tk.Label(
            header, text=ts,
            font=("Consolas", 10), bg=COLORS["bg_card"],
            fg=COLORS["text_dim"]
        ).pack(side="left", padx=(0, 8))

        # Endpoint (se disponível)
        if self.incident.endpoint:
            ep = self.incident.endpoint
            if len(ep) > 55:
                ep = ep[:52] + "..."
            tk.Label(
                header, text=ep,
                font=("Consolas", 10), bg=COLORS["bg_card"],
                fg=COLORS["info"]
            ).pack(side="left", padx=(0, 8))

        # HTTP code
        if self.incident.http_code:
            code_color = COLORS["danger"] if self.incident.http_code >= 500 else COLORS["warning"]
            tk.Label(
                header, text=str(self.incident.http_code),
                font=("Consolas", 10, "bold"), bg=COLORS["bg_card"],
                fg=code_color
            ).pack(side="left", padx=(0, 8))

        # Intervalo desde o último
        if self.incident.interval_from_last is not None:
            tk.Label(
                header, text=f"+{self.incident.interval_from_last:.1f}s",
                font=("Consolas", 9), bg=COLORS["bg_card"],
                fg=COLORS["text_dim"]
            ).pack(side="left")

        # Seta expandir
        self._arrow = tk.Label(
            header, text="▶",
            font=("Consolas", 9), bg=COLORS["bg_card"],
            fg=COLORS["text_dim"]
        )
        self._arrow.pack(side="right", padx=10)

        # ── Corpo expandível ──────────────────────────────────────────────
        self._body = tk.Frame(self, bg=COLORS["bg_secondary"])

        # Linha trigger
        self._add_section(self._body, "Linha que disparou o erro:", [self.incident.trigger_line], COLORS["danger"])

        # Exception extraída
        if self.incident.raw_exception:
            self._add_section(self._body, "Exception:", [self.incident.raw_exception], COLORS["warning"])

        # Contexto antes
        if self.incident.context_before:
            self._add_section(self._body, "Contexto (linhas antes):", self.incident.context_before, COLORS["text_dim"])

        # Contexto depois
        if self.incident.context_after:
            self._add_section(self._body, "Contexto (linhas após):", self.incident.context_after, COLORS["text_dim"])

        # Bind click no header
        for widget in [header] + list(header.winfo_children()):
            widget.bind("<Button-1>", self._toggle)
            widget.bind("<Enter>", lambda e: header.configure(bg=COLORS["bg_hover"]))
            widget.bind("<Leave>", lambda e: header.configure(bg=COLORS["bg_card"]))

        # Borda inferior sutil
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

    def _add_section(self, parent, label: str, lines: List[str], color: str):
        tk.Label(
            parent, text=label,
            font=("Segoe UI", 9, "bold"), bg=COLORS["bg_secondary"],
            fg=COLORS["text_dim"], anchor="w"
        ).pack(fill="x", padx=12, pady=(8, 2))

        text_widget = tk.Text(
            parent, font=("Consolas", 9),
            bg=COLORS["bg"], fg=color,
            relief="flat", wrap="none",
            height=min(len(lines), 8),
            state="normal"
        )
        text_widget.insert("1.0", "\n".join(lines))
        text_widget.configure(state="disabled")
        text_widget.pack(fill="x", padx=12, pady=(0, 8))

    def _toggle(self, event=None):
        self.expanded = not self.expanded
        if self.expanded:
            self._body.pack(fill="x", padx=1, pady=(0, 1))
            self._arrow.configure(text="▼")
        else:
            self._body.pack_forget()
            self._arrow.configure(text="▶")


class NetworkIncidentsTab(tk.Frame):
    """
    Aba completa de Incidentes de Rede.
    Pode ser adicionada diretamente ao Notebook do logcat tool existente.
    """

    def __init__(self, parent, detector: Optional[NetworkIncidentDetector] = None, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.detector = detector or NetworkIncidentDetector(context_before=25, context_after=10)
        self._card_widgets: List[IncidentCard] = []
        self._auto_refresh = True
        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = tk.Frame(self, bg=COLORS["bg_secondary"], height=40)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self._lbl_count = tk.Label(
            toolbar, text="0 incidentes",
            font=("Segoe UI", 10), bg=COLORS["bg_secondary"],
            fg=COLORS["text_dim"]
        )
        self._lbl_count.pack(side="left", padx=12)

        self._lbl_last = tk.Label(
            toolbar, text="",
            font=("Consolas", 9), bg=COLORS["bg_secondary"],
            fg=COLORS["text_dim"]
        )
        self._lbl_last.pack(side="left", padx=8)

        # Botão limpar
        tk.Button(
            toolbar, text="⟳ Limpar",
            font=("Segoe UI", 9), bg=COLORS["bg_card"],
            fg=COLORS["text"], relief="flat", padx=8, pady=2,
            cursor="hand2",
            command=self._clear
        ).pack(side="right", padx=4, pady=6)

        # Botão exportar
        tk.Button(
            toolbar, text="↓ Exportar JSON",
            font=("Segoe UI", 9), bg=COLORS["bg_card"],
            fg=COLORS["text"], relief="flat", padx=8, pady=2,
            cursor="hand2",
            command=self._export
        ).pack(side="right", padx=4, pady=6)

        # Botão análise
        tk.Button(
            toolbar, text="🔍 Analisar",
            font=("Segoe UI", 9), bg=COLORS["accent"],
            fg=COLORS["text_bright"], relief="flat", padx=8, pady=2,
            cursor="hand2",
            command=self._show_analysis
        ).pack(side="right", padx=4, pady=6)

        # ── Painel central: lista de incidentes + painel de análise ───
        paned = tk.PanedWindow(self, orient="horizontal", bg=COLORS["bg"],
                               sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        # Lista de incidentes
        left_frame = tk.Frame(paned, bg=COLORS["bg"])
        paned.add(left_frame, minsize=400)

        canvas = tk.Canvas(left_frame, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        self._cards_frame = tk.Frame(canvas, bg=COLORS["bg"])

        self._cards_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self._cards_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._canvas = canvas

        # Mousewheel
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Estado vazio
        self._empty_label = tk.Label(
            self._cards_frame,
            text="Nenhum incidente de rede detectado ainda.\nOs erros aparecerão aqui automaticamente.",
            font=("Segoe UI", 11), bg=COLORS["bg"],
            fg=COLORS["text_dim"], justify="center"
        )
        self._empty_label.pack(pady=60)

        # Painel de análise (direita)
        right_frame = tk.Frame(paned, bg=COLORS["bg_secondary"])
        paned.add(right_frame, minsize=260)
        self._build_analysis_panel(right_frame)

    def _build_analysis_panel(self, parent):
        tk.Label(
            parent, text="Análise",
            font=("Segoe UI", 11, "bold"), bg=COLORS["bg_secondary"],
            fg=COLORS["text_bright"]
        ).pack(anchor="w", padx=12, pady=(12, 4))

        tk.Frame(parent, bg=COLORS["border"], height=1).pack(fill="x", padx=12)

        # Métricas
        metrics_frame = tk.Frame(parent, bg=COLORS["bg_secondary"])
        metrics_frame.pack(fill="x", padx=12, pady=8)

        self._metric_widgets = {}
        metrics = [
            ("total",    "Total"),
            ("interval", "Intervalo médio"),
            ("pattern",  "Padrão"),
        ]
        for key, label in metrics:
            row = tk.Frame(metrics_frame, bg=COLORS["bg_secondary"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label + ":", font=("Segoe UI", 9),
                     bg=COLORS["bg_secondary"], fg=COLORS["text_dim"],
                     anchor="w", width=16).pack(side="left")
            lbl = tk.Label(row, text="—", font=("Segoe UI", 9, "bold"),
                           bg=COLORS["bg_secondary"], fg=COLORS["text"],
                           anchor="w", wraplength=180, justify="left")
            lbl.pack(side="left", fill="x", expand=True)
            self._metric_widgets[key] = lbl

        tk.Frame(parent, bg=COLORS["border"], height=1).pack(fill="x", padx=12)

        # Distribuição de categorias
        tk.Label(
            parent, text="Categorias",
            font=("Segoe UI", 10, "bold"), bg=COLORS["bg_secondary"],
            fg=COLORS["text"]
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self._cat_frame = tk.Frame(parent, bg=COLORS["bg_secondary"])
        self._cat_frame.pack(fill="x", padx=12)

        tk.Frame(parent, bg=COLORS["border"], height=1).pack(fill="x", padx=12, pady=8)

        # Causa raiz
        tk.Label(
            parent, text="Causa mais provável",
            font=("Segoe UI", 10, "bold"), bg=COLORS["bg_secondary"],
            fg=COLORS["text"]
        ).pack(anchor="w", padx=12)

        self._cause_text = tk.Text(
            parent, font=("Segoe UI", 9),
            bg=COLORS["bg"], fg=COLORS["warning"],
            relief="flat", wrap="word",
            height=7, state="disabled",
            padx=8, pady=8
        )
        self._cause_text.pack(fill="x", padx=12, pady=4)

        # Endpoints afetados
        tk.Label(
            parent, text="Endpoints afetados",
            font=("Segoe UI", 10, "bold"), bg=COLORS["bg_secondary"],
            fg=COLORS["text"]
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self._endpoints_text = tk.Text(
            parent, font=("Consolas", 8),
            bg=COLORS["bg"], fg=COLORS["info"],
            relief="flat", wrap="word",
            height=5, state="disabled",
            padx=8, pady=8
        )
        self._endpoints_text.pack(fill="x", padx=12, pady=(0, 12))

    # ------------------------------------------------------------------
    # API pública — chamada pelo logcat thread
    # ------------------------------------------------------------------

    def feed_line(self, line: str):
        """Alimenta uma linha do logcat. Thread-safe."""
        incident = self.detector.feed(line)
        if incident:
            self.after(0, self._add_incident_card, incident)
            self.after(0, self._refresh_analysis)

    def add_incident(self, incident: NetworkIncident):
        """Adiciona incidente diretamente (se já detectado externamente)."""
        self.after(0, self._add_incident_card, incident)
        self.after(0, self._refresh_analysis)

    # ------------------------------------------------------------------
    # Internos de UI
    # ------------------------------------------------------------------

    def _add_incident_card(self, incident: NetworkIncident):
        if self._empty_label.winfo_ismapped():
            self._empty_label.pack_forget()

        idx = len(self._card_widgets)
        card = IncidentCard(self._cards_frame, incident, idx)
        card.pack(fill="x", padx=4, pady=2)
        self._card_widgets.append(card)

        # Atualiza contador no toolbar
        count = len(self._card_widgets)
        self._lbl_count.configure(
            text=f"{count} incidente{'s' if count != 1 else ''}",
            fg=COLORS["danger"] if count > 0 else COLORS["text_dim"]
        )
        self._lbl_last.configure(
            text=f"último: {incident.timestamp.strftime('%H:%M:%S')} — {incident.category.value}"
        )

        # Auto-scroll para o final
        self._canvas.update_idletasks()
        self._canvas.yview_moveto(1.0)

    def _refresh_analysis(self):
        analysis = self.detector.analyze()
        if not analysis["total"]:
            return

        self._metric_widgets["total"].configure(
            text=str(analysis["total"]),
            fg=COLORS["danger"]
        )
        if analysis["avg_interval_seconds"]:
            self._metric_widgets["interval"].configure(
                text=f"{analysis['avg_interval_seconds']}s",
                fg=COLORS["warning"]
            )
        if analysis["pattern"]:
            self._metric_widgets["pattern"].configure(
                text=analysis["pattern"],
                fg=COLORS["info"]
            )

        # Categorias
        for w in self._cat_frame.winfo_children():
            w.destroy()

        for cat, cnt in sorted(analysis["categories"].items(), key=lambda x: -x[1]):
            row = tk.Frame(self._cat_frame, bg=COLORS["bg_secondary"])
            row.pack(fill="x", pady=2)
            color = CATEGORY_COLORS.get(cat, COLORS["text"])
            tk.Label(row, text=f"● {cat}", font=("Segoe UI", 9),
                     bg=COLORS["bg_secondary"], fg=color,
                     anchor="w").pack(side="left")
            tk.Label(row, text=str(cnt), font=("Segoe UI", 9, "bold"),
                     bg=COLORS["bg_secondary"], fg=color,
                     anchor="e").pack(side="right")

        # Causa raiz
        cause = analysis.get("most_likely_cause") or "—"
        self._cause_text.configure(state="normal")
        self._cause_text.delete("1.0", "end")
        self._cause_text.insert("1.0", cause)
        self._cause_text.configure(state="disabled")

        # Endpoints
        endpoints = analysis.get("endpoints") or []
        self._endpoints_text.configure(state="normal")
        self._endpoints_text.delete("1.0", "end")
        self._endpoints_text.insert("1.0", "\n".join(endpoints) if endpoints else "—")
        self._endpoints_text.configure(state="disabled")

    def _show_analysis(self):
        analysis = self.detector.analyze()
        if not analysis["total"]:
            messagebox.showinfo("Análise", "Nenhum incidente detectado ainda.")
            return

        win = tk.Toplevel(self)
        win.title("Análise de Incidentes de Rede")
        win.configure(bg=COLORS["bg"])
        win.geometry("700x500")

        txt = scrolledtext.ScrolledText(
            win, font=("Consolas", 10),
            bg=COLORS["bg"], fg=COLORS["text"],
            relief="flat", wrap="word"
        )
        txt.pack(fill="both", expand=True, padx=12, pady=12)

        report = json.dumps(analysis, ensure_ascii=False, indent=2)
        txt.insert("1.0", report)
        txt.configure(state="disabled")

    def _clear(self):
        if messagebox.askyesno("Limpar", "Limpar todos os incidentes?"):
            self.detector.clear()
            for card in self._card_widgets:
                card.destroy()
            self._card_widgets.clear()
            self._empty_label.pack(pady=60)
            self._lbl_count.configure(text="0 incidentes", fg=COLORS["text_dim"])
            self._lbl_last.configure(text="")
            for key in self._metric_widgets:
                self._metric_widgets[key].configure(text="—")
            for w in self._cat_frame.winfo_children():
                w.destroy()

    def _export(self):
        path = self.detector.export_report("network_incidents.json")
        messagebox.showinfo("Exportado", f"Relatório salvo em:\n{path}")


# ---------------------------------------------------------------------------
# Demo standalone
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import random
    import time

    root = tk.Tk()
    root.title("Network Incidents — Demo")
    root.geometry("1100x700")
    root.configure(bg=COLORS["bg"])

    tab = NetworkIncidentsTab(root)
    tab.pack(fill="both", expand=True)

    # Simula linhas de log chegando
    FAKE_LOGS = [
        "[09:57:07] I/OkHttp: --> GET https://api.amplawfm.overit.it/v2/jobs?status=open",
        "[09:57:07] E/OkHttp: javax.net.ssl.SSLHandshakeException: Handshake failed",
        "[09:57:08] W/Retrofit: java.net.SocketTimeoutException: connect timed out",
        "[09:57:12] I/OkHttp: --> POST https://api.amplawfm.overit.it/v2/forms/submit",
        "[09:57:12] E/OkHttp: java.net.UnknownHostException: Unable to resolve host",
        "[09:57:15] W/OkHttp: HTTP 503 https://api.amplawfm.overit.it/v2/sync",
        "[09:57:30] E/OkHttp: javax.net.ssl.SSLPeerUnverifiedException: Certificate pinning failure",
        "[09:58:01] E/OkHttp: java.net.ConnectException: Connection refused",
    ]

    def feed_demo():
        for line in FAKE_LOGS:
            tab.feed_line(line)
            time.sleep(0.3)

    threading.Thread(target=feed_demo, daemon=True).start()
    root.mainloop()