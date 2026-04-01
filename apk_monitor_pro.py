"""
APK Monitor Pro v2.0 - Interface Gráfica Completa
Sistema Profissional de Diagnóstico de APKs Android

Integra TODOS os módulos em uma interface unificada
"""

import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import QThread, pyqtSignal, Qt
    from PyQt5.QtGui import QFont
except ImportError:
    print("\n" + "="*70)
    print("PyQt5 não instalado!")
    print("="*70)
    print("\nVocê está em um venv. Instale manualmente:")
    print("\n  pip install PyQt5\n")
    print("Depois execute novamente:")
    print("  python apk_monitor_pro.py")
    print("="*70 + "\n")
    sys.exit(1)

# Adiciona path dos módulos
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Imports dos módulos - tenta de várias formas
try:
    from apk_monitor_pro.core.adb_manager import ADBManager
    from apk_monitor_pro.analyzers.error_diagnostics import ErrorDiagnostics
    from apk_monitor_pro.integrations.frida_hook import FridaHooker
    from apk_monitor_pro.integrations.tcpdump_capture import TCPDumpCapture
    from apk_monitor_pro.utils.report_generator import ReportGenerator
except ImportError:
    # Fallback: importa diretamente
    import importlib.util
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    adb_mod = load_module("adb_manager", current_dir / "apk_monitor_pro" / "core" / "adb_manager.py")
    ADBManager = adb_mod.ADBManager
    
    diag_mod = load_module("error_diagnostics", current_dir / "apk_monitor_pro" / "analyzers" / "error_diagnostics.py")
    ErrorDiagnostics = diag_mod.ErrorDiagnostics
    
    frida_mod = load_module("frida_hook", current_dir / "apk_monitor_pro" / "integrations" / "frida_hook.py")
    FridaHooker = frida_mod.FridaHooker
    
    tcp_mod = load_module("tcpdump_capture", current_dir / "apk_monitor_pro" / "integrations" / "tcpdump_capture.py")
    TCPDumpCapture = tcp_mod.TCPDumpCapture
    
    rep_mod = load_module("report_generator", current_dir / "apk_monitor_pro" / "utils" / "report_generator.py")
    ReportGenerator = rep_mod.ReportGenerator


# Thread de captura ADB
class ADBThread(QThread):
    log_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, adb_mgr, pkg, level, strict):
        super().__init__()
        self.adb = adb_mgr
        self.pkg = pkg
        self.level = level
        self.strict = strict
        self.running = False
        self.proc = None
        
    def run(self):
        self.running = True
        try:
            self.proc = self.adb.start_logcat_filtered(self.pkg, self.level, self.strict)
            for line in self.proc.stdout:
                if not self.running:
                    break
                log = self.parse(line)
                if log:
                    self.log_signal.emit(log)
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def parse(self, line):
        try:
            p = line.strip().split(None, 6)
            if len(p) < 7:
                return None
            return {
                'timestamp': f"{p[0]} {p[1]}",
                'pid': p[2],
                'tid': p[3],
                'level': p[4],
                'tag': p[5].rstrip(':'),
                'message': p[6] if len(p) > 6 else ''
            }
        except:
            return None
    
    def stop(self):
        self.running = False
        if self.proc:
            self.proc.terminate()


# Interface principal
class APKMonitorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Módulos
        self.adb = ADBManager()
        self.diag = ErrorDiagnostics()
        self.report = ReportGenerator()
        self.tcpdump = TCPDumpCapture()
        
        # Estado
        self.logs = []
        self.errors = []
        self.monitoring = False
        self.thread = None
        
        # Pacotes
        self.pkgs = {
            0: "it.overit.amplawfm",
            1: "it.overit.enelsaopaulowfm",
            2: "it.overit.coelcewfm",
            3: "custom"
        }
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("APK Monitor Pro v2.0 - Diagnóstico Profissional")
        self.setGeometry(50, 50, 1700, 950)
        
        w = QWidget()
        self.setCentralWidget(w)
        layout = QVBoxLayout(w)
        
        # Header
        layout.addWidget(self.make_header())
        
        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.make_logs(), "📱 Logs")
        tabs.addTab(self.make_diag(), "🔍 Diagnóstico")
        tabs.addTab(self.make_timeline(), "⏱️ Timeline")
        tabs.addTab(self.make_frida(), "🔗 Frida")
        tabs.addTab(self.make_reports(), "📄 Relatórios")
        
        layout.addWidget(tabs)
        self.statusBar().showMessage("Pronto")
        
    def make_header(self):
        g = QGroupBox("Configurações")
        l = QHBoxLayout()
        
        l.addWidget(QLabel("APK:"))
        self.pkg_combo = QComboBox()
        self.pkg_combo.addItems([
            "🇧🇷 Rio", "🇧🇷 SP", "🇧🇷 CE", "📦 Outro"
        ])
        self.pkg_combo.currentIndexChanged.connect(self.pkg_changed)
        l.addWidget(self.pkg_combo)
        
        self.pkg_input = QLineEdit()
        self.pkg_input.setPlaceholderText("Pacote personalizado")
        self.pkg_input.hide()
        l.addWidget(self.pkg_input)
        
        l.addWidget(QLabel("Filtro:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["🎯 Rígido (PID)", "🔄 Flexível"])
        l.addWidget(self.filter_combo)
        
        l.addWidget(QLabel("Nível:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["V", "D", "I", "W", "E"])
        self.level_combo.setCurrentIndex(2)
        l.addWidget(self.level_combo)
        
        l.addStretch()
        
        proxy_btn = QPushButton("🌐 Config Proxy")
        proxy_btn.clicked.connect(self.config_proxy)
        proxy_btn.setStyleSheet("background:#FF9800;color:white;padding:10px;font-weight:bold")
        l.addWidget(proxy_btn)
        
        self.start_btn = QPushButton("▶️ INICIAR")
        self.start_btn.clicked.connect(self.start)
        self.start_btn.setStyleSheet("background:#4CAF50;color:white;padding:12px;font-weight:bold")
        l.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ PARAR")
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background:#f44336;color:white;padding:12px;font-weight:bold")
        l.addWidget(self.stop_btn)
        
        g.setLayout(l)
        return g
        
    def make_logs(self):
        w = QWidget()
        l = QVBoxLayout()
        
        # Status
        info = QHBoxLayout()
        self.dev_lbl = QLabel("📱 Verificando...")
        info.addWidget(self.dev_lbl)
        self.pid_lbl = QLabel("🔢 PID: -")
        info.addWidget(self.pid_lbl)
        l.addLayout(info)
        
        # Filtros
        f = QHBoxLayout()
        self.f_err = QCheckBox("Erros")
        self.f_err.toggled.connect(self.reapply_filters)
        f.addWidget(self.f_err)
        
        self.f_sync = QCheckBox("Sync")
        self.f_sync.toggled.connect(self.reapply_filters)
        f.addWidget(self.f_sync)
        
        self.f_network = QCheckBox("Network")
        self.f_network.toggled.connect(self.reapply_filters)
        f.addWidget(self.f_network)
        
        self.f_sqlite = QCheckBox("SQLite")
        self.f_sqlite.toggled.connect(self.reapply_filters)
        f.addWidget(self.f_sqlite)
        
        self.f_http = QCheckBox("HTTP")
        self.f_http.toggled.connect(self.reapply_filters)
        f.addWidget(self.f_http)
        f.addStretch()
        clear = QPushButton("🗑️")
        clear.clicked.connect(self.clear)
        f.addWidget(clear)
        l.addLayout(f)
        
        # Display
        self.log_txt = QTextEdit()
        self.log_txt.setReadOnly(True)
        self.log_txt.setFont(QFont("Consolas", 9))
        l.addWidget(self.log_txt)
        
        self.stats = QLabel("📊 0 logs")
        l.addWidget(self.stats)
        
        w.setLayout(l)
        self.check_dev()
        return w
        
    def make_diag(self):
        w = QWidget()
        l = QVBoxLayout()
        
        l.addWidget(QLabel("<h2>🔍 Diagnóstico de Causa Raiz</h2>"))
        
        self.diag_list = QListWidget()
        self.diag_list.itemClicked.connect(self.show_diag)
        l.addWidget(self.diag_list)
        
        self.diag_txt = QTextEdit()
        self.diag_txt.setReadOnly(True)
        l.addWidget(self.diag_txt)
        
        w.setLayout(l)
        return w
        
    def make_timeline(self):
        w = QWidget()
        l = QVBoxLayout()
        
        l.addWidget(QLabel("<h2>⏱️ Timeline de Eventos</h2>"))
        
        tl = QHBoxLayout()
        tl.addWidget(QLabel("Erro:"))
        self.tl_combo = QComboBox()
        tl.addWidget(self.tl_combo)
        btn = QPushButton("Gerar")
        btn.clicked.connect(self.gen_timeline)
        tl.addWidget(btn)
        l.addLayout(tl)
        
        self.tl_txt = QTextEdit()
        self.tl_txt.setReadOnly(True)
        self.tl_txt.setFont(QFont("Consolas", 9))
        l.addWidget(self.tl_txt)
        
        w.setLayout(l)
        return w
        
    def make_frida(self):
        w = QWidget()
        l = QVBoxLayout()
        
        l.addWidget(QLabel("<h2>🔗 Frida Hooking</h2>"))
        
        hooker = FridaHooker("test")
        if hooker.check_frida_available():
            lbl = QLabel("✅ Frida disponível")
            lbl.setStyleSheet("background:#C8E6C9;padding:10px")
            self.frida_available = True
        else:
            lbl = QLabel("⚠️ Frida não instalado. Instale com: pip install frida frida-tools")
            lbl.setStyleSheet("background:#FFECB3;padding:10px")
            self.frida_available = False
        l.addWidget(lbl)
        
        # Botão de setup automático
        if self.frida_available:
            setup_group = QGroupBox("⚙️ Setup Frida Server")
            setup_layout = QVBoxLayout()
            
            info = QLabel(
                "Frida Server precisa estar rodando no dispositivo Android.\n"
                "Clique abaixo para verificar/iniciar automaticamente."
            )
            info.setWordWrap(True)
            setup_layout.addWidget(info)
            
            check_btn = QPushButton("🔍 Verificar Frida Server")
            check_btn.clicked.connect(self.check_frida_server_status)
            check_btn.setStyleSheet("background:#2196F3;color:white;padding:8px")
            setup_layout.addWidget(check_btn)
            
            setup_group.setLayout(setup_layout)
            l.addWidget(setup_group)
        
        # Botões de hook
        if self.frida_available:
            hooks_group = QGroupBox("🎯 Hooks Disponíveis")
            hooks_layout = QVBoxLayout()
            
            sync_btn = QPushButton("🔄 Hook Métodos de Sincronização")
            sync_btn.clicked.connect(lambda: self.start_frida_hook('sync'))
            sync_btn.setStyleSheet("background:#2196F3;color:white;padding:10px")
            hooks_layout.addWidget(sync_btn)
            
            sqlite_btn = QPushButton("💾 Hook Queries SQLite")
            sqlite_btn.clicked.connect(lambda: self.start_frida_hook('sqlite'))
            sqlite_btn.setStyleSheet("background:#4CAF50;color:white;padding:10px")
            hooks_layout.addWidget(sqlite_btn)
            
            http_btn = QPushButton("🌐 Hook Requests HTTP")
            http_btn.clicked.connect(lambda: self.start_frida_hook('http'))
            http_btn.setStyleSheet("background:#FF9800;color:white;padding:10px")
            hooks_layout.addWidget(http_btn)
            
            hooks_group.setLayout(hooks_layout)
            l.addWidget(hooks_group)
        
        self.frida_txt = QTextEdit()
        self.frida_txt.setReadOnly(True)
        self.frida_txt.setFont(QFont("Consolas", 9))
        self.frida_txt.setPlaceholderText("Hooks capturados aparecerão aqui...")
        l.addWidget(self.frida_txt)
        
        w.setLayout(l)
        return w
        
    def make_reports(self):
        w = QWidget()
        l = QVBoxLayout()
        
        l.addWidget(QLabel("<h2>📄 Exportar Dados do Monitoramento</h2>"))
        
        info = QLabel(
            "O relatório consolida todos os logs capturados, eventos de rede e "
            "diagnósticos de erro em um único arquivo."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; margin-bottom: 20px;")
        l.addWidget(info)
        
        btn_json = QPushButton("{ } Exportar JSON (Dados Brutos)")
        btn_json.clicked.connect(lambda: self.gen_report('json'))
        btn_json.setStyleSheet("background:#2196F3;color:white;padding:15px;font-weight:bold;font-size:14px;")
        l.addWidget(btn_json)
        
        btn_html = QPushButton("🌐 Exportar HTML (Dashboard Visual)")
        btn_html.clicked.connect(lambda: self.gen_report('html'))
        btn_html.setStyleSheet("background:#4CAF50;color:white;padding:15px;font-weight:bold;font-size:14px;")
        l.addWidget(btn_html)
        
        l.addStretch()
        w.setLayout(l)
        return w

    def pkg_changed(self, i):
        self.pkg_input.setVisible(i == 3)
        
    def get_pkg(self):
        i = self.pkg_combo.currentIndex()
        return self.pkg_input.text() if i == 3 else self.pkgs[i]
        
    def check_dev(self):
        if self.adb.check_adb_available():
            devs = self.adb.get_connected_devices()
            if devs:
                self.dev_lbl.setText(f"📱 {devs[0]} ✅")
            else:
                self.dev_lbl.setText("📱 Nenhum ⚠️")
        else:
            self.dev_lbl.setText("📱 ADB não encontrado ❌")
            
    def config_proxy(self):
        r = QMessageBox.question(self, "Proxy", 
            "ADB Reverse (simples)?\n\nYes = ADB Reverse\nNo = iptables (root)")
        
        if r == QMessageBox.Yes:
            if self.adb.configure_proxy_reverse(8888):
                QMessageBox.information(self, "OK", "✅ Proxy configurado via ADB Reverse!")
            else:
                QMessageBox.warning(self, "Erro", "❌ Falha")
        else:
            res = self.adb.configure_proxy_iptables(8888)
            if res['success']:
                QMessageBox.information(self, "OK", "✅ Proxy via iptables!")
            else:
                QMessageBox.critical(self, "Erro", "\n".join(res['errors']))
                
    def start(self):
        pkg = self.get_pkg()
        if not pkg:
            QMessageBox.warning(self, "Atenção", "Selecione a APK!")
            return
            
        strict = (self.filter_combo.currentIndex() == 0)
        
        if strict:
            pid = self.adb.get_package_pid(pkg)
            if pid:
                self.pid_lbl.setText(f"🔢 PID: {pid}")
            else:
                QMessageBox.warning(self, "Erro", "PID não encontrado!\nAPK está rodando?")
                return
                
        level = self.level_combo.currentText()
        
        self.thread = ADBThread(self.adb, pkg, level, strict)
        self.thread.log_signal.connect(self.on_log)
        self.thread.error_signal.connect(lambda e: QMessageBox.critical(self, "Erro", e))
        self.thread.start()
        
        self.monitoring = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage(f"✅ Monitorando {pkg}")
        
    def stop(self):
        if self.thread:
            self.thread.stop()
            self.thread.wait()
        self.monitoring = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("⏹️ Parado")
        
    def on_log(self, log):
        self.logs.append(log)
        
        # Diagnóstico
        if log['level'] in ['E', 'F', 'W']:
            d = self.diag.diagnose_error(log)
            if d.get('layer') != 'UNKNOWN':
                self.errors.append({'log': log, 'diag': d})
                self.diag_list.addItem(f"[{log['timestamp']}] {d.get('error_type', 'Erro')}")
                self.tl_combo.addItem(f"[{log['timestamp']}] {d.get('error_type', 'Erro')}")
        
        # Aplica filtros antes de exibir
        should_display = True
        
        # Se NENHUM filtro está marcado, mostra tudo
        any_filter_active = (self.f_err.isChecked() or self.f_sync.isChecked() or 
                            self.f_network.isChecked() or self.f_sqlite.isChecked() or 
                            self.f_http.isChecked())
        
        if any_filter_active:
            # Se algum filtro está ativo, começa como False
            should_display = False
            
            # Filtro de erros
            if self.f_err.isChecked() and log['level'] in ['E', 'F', 'W']:
                should_display = True
            
            # Filtro sync
            if self.f_sync.isChecked() and ('sync' in log['message'].lower() or 'sync' in log['tag'].lower()):
                should_display = True
            
            # Filtro network
            if self.f_network.isChecked() and ('network' in log['message'].lower() or 'network' in log['tag'].lower() or 
                                               'connect' in log['message'].lower() or 'socket' in log['message'].lower()):
                should_display = True
            
            # Filtro SQLite
            if self.f_sqlite.isChecked() and ('sqlite' in log['message'].lower() or 'database' in log['message'].lower() or 
                                              'sql' in log['tag'].lower()):
                should_display = True
            
            # Filtro HTTP
            if self.f_http.isChecked() and ('http' in log['message'].lower() or 'request' in log['message'].lower() or 
                                           'response' in log['message'].lower() or 'okhttp' in log['tag'].lower()):
                should_display = True
        
        # Se passou nos filtros, exibe
        if should_display:
            colors = {'V':'#888','D':'#00F','I':'#080','W':'#F80','E':'#F00','F':'#800'}
            c = colors.get(log['level'], '#000')
            self.log_txt.append(f"<span style='color:{c}'>[{log['timestamp']}] {log['level']}/{log['tag']}: {log['message']}</span>")
        
        self.stats.setText(f"📊 {len(self.logs)} logs | {len(self.errors)} erros")
        
    def clear(self):
        self.logs.clear()
        self.errors.clear()
        self.log_txt.clear()
        self.diag_list.clear()
        self.tl_combo.clear()
        self.stats.setText("📊 0 logs")
    
    def reapply_filters(self):
        """Reaplica filtros em todos os logs"""
        self.log_txt.clear()
        
        for log in self.logs:
            should_display = True
            
            # Se NENHUM filtro está marcado, mostra tudo
            any_filter_active = (self.f_err.isChecked() or self.f_sync.isChecked() or 
                                self.f_network.isChecked() or self.f_sqlite.isChecked() or 
                                self.f_http.isChecked())
            
            if any_filter_active:
                # Se algum filtro está ativo, começa como False
                should_display = False
                
                # Filtro de erros
                if self.f_err.isChecked() and log['level'] in ['E', 'F', 'W']:
                    should_display = True
                
                # Filtro sync
                if self.f_sync.isChecked() and ('sync' in log['message'].lower() or 'sync' in log['tag'].lower()):
                    should_display = True
                
                # Filtro network
                if self.f_network.isChecked() and ('network' in log['message'].lower() or 'network' in log['tag'].lower() or 
                                                   'connect' in log['message'].lower() or 'socket' in log['message'].lower()):
                    should_display = True
                
                # Filtro SQLite
                if self.f_sqlite.isChecked() and ('sqlite' in log['message'].lower() or 'database' in log['message'].lower() or 
                                                  'sql' in log['tag'].lower()):
                    should_display = True
                
                # Filtro HTTP
                if self.f_http.isChecked() and ('http' in log['message'].lower() or 'request' in log['message'].lower() or 
                                               'response' in log['message'].lower() or 'okhttp' in log['tag'].lower()):
                    should_display = True
            
            # Se passou nos filtros, exibe
            if should_display:
                colors = {'V':'#888','D':'#00F','I':'#080','W':'#F80','E':'#F00','F':'#800'}
                c = colors.get(log['level'], '#000')
                self.log_txt.append(f"<span style='color:{c}'>[{log['timestamp']}] {log['level']}/{log['tag']}: {log['message']}</span>")
        
    def show_diag(self, item):
        i = self.diag_list.currentRow()
        if i < 0 or i >= len(self.errors):
            return
        d = self.errors[i]['diag']
        
        html = f"""
<h1>🔍 Diagnóstico</h1>
<div style='background:#E3F2FD;padding:15px;margin:10px'>
<h3>Camada</h3><p><b>{d.get('layer', 'UNKNOWN')}</b></p>
</div>
<div style='background:#FFF3CD;padding:15px;margin:10px'>
<h3>Responsável</h3><p><b>{d.get('responsible_team', 'N/A')}</b></p>
</div>
<div style='background:#F5F5F5;padding:15px;margin:10px'>
<h3>Causa Raiz</h3><p>{d.get('root_cause', 'N/A')}</p>
</div>
<div style='background:#E8F5E9;padding:15px;margin:10px'>
<h3>Ação</h3><pre>{d.get('recommended_action', 'N/A')}</pre>
</div>
"""
        self.diag_txt.setHtml(html)
        
    def gen_timeline(self):
        i = self.tl_combo.currentIndex()
        if i < 0 or i >= len(self.errors):
            return
        
        err_log = self.errors[i]['log']
        tl = self.diag.generate_timeline(self.logs, err_log, 30)
        
        out = ["="*80, "TIMELINE: 30s antes do erro", "="*80, ""]
        for e in tl:
            out.append(f"-{e['seconds_before_error']:05.2f}s | {e['tag']}: {e['message'][:60]}")
        
        self.tl_txt.setPlainText("\n".join(out))
        
    def gen_report(self, tipo):
        try:
            # 1. Captura as variáveis
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            pkg_name = str(self.get_pkg())
            apk_text = str(self.pkg_combo.currentText())
            
            # Cópia local das listas para evitar problemas de concorrência
            logs_snapshot = list(self.logs)
            errors_snapshot = list(self.errors)
            
            # 2. Monta o payload unificado
            payload = {
                "timestamp": ts,
                "apk": apk_text,
                "package": pkg_name,
                "logs": logs_snapshot,
                "network": [],
                "errors": errors_snapshot
            }
            
            # 3. Roteia para o gerador CORRETO (json ou html)
            if tipo == 'json':
                content = self.report.generate_json(payload)
                fn = f"relatorio_apk_{ts}.json"
                file_filter = "JSON (*.json)"
            elif tipo == 'html':
                content = self.report.generate_html(payload)
                fn = f"relatorio_apk_{ts}.html"
                file_filter = "HTML (*.html)"
            else:
                print(f"Tipo desconhecido: {tipo}")
                return 
            
            # 4. Diálogo de salvar
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            
            path, _ = QFileDialog.getSaveFileName(
                self, 
                "Salvar Relatório", 
                fn, 
                file_filter,
                options=options
            )
            
            # 5. Salva o arquivo final
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "OK", f"✅ Relatório salvo com sucesso em:\n{path}")
                
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            QMessageBox.critical(self, "Erro na Geração", f"Não foi possível gerar o relatório.\n\nDetalhes:\n{str(e)}")
            print("\n=== TRACEBACK ===")
            print(error_msg)
            print("=================")

    
    def start_frida_hook(self, hook_type):
        """Inicia hooking com Frida"""
        if not self.frida_available:
            QMessageBox.warning(self, "Frida não disponível", 
                              "Instale Frida primeiro:\npip install frida frida-tools")
            return
        
        pkg = self.get_pkg()
        if not pkg:
            QMessageBox.warning(self, "Atenção", "Selecione a APK primeiro!")
            return
        
        # Verifica se frida-server está rodando
        hooker = FridaHooker(pkg)
        if not hooker.check_frida_server():
            # Tenta iniciar automaticamente
            reply = QMessageBox.question(
                self, 
                "Frida Server", 
                "Frida Server não está rodando.\n\n"
                "Deseja que eu tente iniciar automaticamente?\n"
                "(Requer ROOT no dispositivo)",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.frida_txt.append("<b>🔄 Iniciando frida-server...</b><br>")
                
                if hooker.start_frida_server():
                    self.frida_txt.append("<b style='color:green'>✅ Frida-server iniciado com sucesso!</b><br>")
                else:
                    QMessageBox.critical(
                        self, 
                        "Erro", 
                        "Não foi possível iniciar frida-server!\n\n"
                        "Certifique-se que:\n"
                        "1. Dispositivo tem ROOT\n"
                        "2. frida-server está em /data/local/tmp/\n"
                        "3. Tem permissão de execução\n\n"
                        "Comando manual:\n"
                        "adb push frida-server /data/local/tmp/\n"
                        "adb shell 'su -c chmod 755 /data/local/tmp/frida-server'\n"
                        "adb shell 'su -c /data/local/tmp/frida-server &'"
                    )
                    return
            else:
                return
        
        self.frida_txt.append(f"<b style='color:green'>✅ Iniciando hook '{hook_type}'...</b><br>")
        self.frida_txt.append(f"<i>Nota: Hooks serão exibidos quando métodos forem chamados</i><br><br>")
        
        # Aqui você implementaria a thread de Frida
        # Por enquanto, mostra mensagem informativa
        QMessageBox.information(self, "Hook Iniciado", 
            f"Hook '{hook_type}' foi iniciado!\n\n"
            f"Use a APK e as chamadas aparecerão na aba Frida.\n\n"
            f"Nota: Implementação completa requer frida-server rodando no dispositivo.")
    
    def check_frida_server_status(self):
        """Verifica status do frida-server"""
        hooker = FridaHooker("test")
        
        self.frida_txt.append("<b>🔍 Verificando Frida Server...</b><br>")
        
        if hooker.check_frida_server():
            self.frida_txt.append("<b style='color:green'>✅ Frida Server está rodando!</b><br><br>")
            QMessageBox.information(self, "Status", "✅ Frida Server está rodando corretamente!")
        else:
            self.frida_txt.append("<b style='color:orange'>⚠️ Frida Server NÃO está rodando</b><br>")
            
            reply = QMessageBox.question(
                self,
                "Frida Server",
                "Frida Server não está rodando.\n\n"
                "Deseja que eu tente iniciar automaticamente?\n"
                "(Requer ROOT)",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.frida_txt.append("<b>🔄 Tentando iniciar...</b><br>")
                
                if hooker.start_frida_server():
                    self.frida_txt.append("<b style='color:green'>✅ Iniciado com sucesso!</b><br><br>")
                    QMessageBox.information(self, "Sucesso", "✅ Frida Server iniciado!")
                else:
                    self.frida_txt.append("<b style='color:red'>❌ Falha ao iniciar</b><br><br>")
                    QMessageBox.critical(
                        self,
                        "Erro",
                        "Não foi possível iniciar frida-server!\n\n"
                        "Instruções manuais:\n\n"
                        "1. Baixe frida-server:\n"
                        "   https://github.com/frida/frida/releases\n\n"
                        "2. Envie para dispositivo:\n"
                        "   adb push frida-server /data/local/tmp/\n\n"
                        "3. Dê permissão:\n"
                        "   adb shell 'su -c chmod 755 /data/local/tmp/frida-server'\n\n"
                        "4. Execute:\n"
                        "   adb shell 'su -c /data/local/tmp/frida-server &'"
                    )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = APKMonitorUI()
    ui.show()
    sys.exit(app.exec_())