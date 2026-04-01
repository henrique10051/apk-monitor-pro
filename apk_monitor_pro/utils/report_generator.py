"""
Report Generator - Exportação Unificada
Gera saídas em JSON e HTML Baseado no Payload Completo
"""

import json
from typing import Dict, List
from datetime import datetime

class ReportGenerator:
    """Gerador de relatórios (JSON e HTML)"""

    def _get_log_context_html(self, all_logs: List[Dict], target_log: Dict, context_size: int = 5) -> str:
        """Gera o bloco HTML simulando o terminal do Android Studio (Logcat)"""
        if not all_logs or not target_log:
            return "<div style='color:#A9B7C6;'><i>Logs de contexto não disponíveis.</i></div>"
            
        target_idx = -1
        for i, log in enumerate(all_logs):
            if log == target_log or (log.get('timestamp') == target_log.get('timestamp') and log.get('message') == target_log.get('message')):
                target_idx = i
                break
                
        if target_idx == -1:
            context_logs = [target_log]
        else:
            start_idx = max(0, target_idx - context_size)
            end_idx = min(len(all_logs), target_idx + context_size + 1)
            context_logs = all_logs[start_idx:end_idx]

        out_lines = []
        for log in context_logs:
            color = "#A9B7C6" 
            lvl = log.get('level', 'V')
            if lvl == 'I': color = "#6A8759"
            elif lvl == 'W': color = "#BBB529"
            elif lvl in ['E', 'F']: color = "#CC666E"
            
            is_target = (log == target_log)
            bg = "background-color: rgba(204, 102, 110, 0.25); border-left: 3px solid #CC666E;" if is_target else "border-left: 3px solid transparent;"
            
            msg = str(log.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')
            
            line = f"<div style='color: {color}; {bg} padding: 2px 5px; margin: 1px 0;'>[{log.get('timestamp', '')}] {lvl}/{log.get('tag', '')}({log.get('pid', '')}:{log.get('tid', '')}): {msg}</div>"
            out_lines.append(line)
            
        return "\n".join(out_lines)

    def generate_json(self, data: dict) -> str:
        """Exporta os dados brutos estruturados"""
        # O default=str é a mágica que impede o programa de fechar por erros de tipo!
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    def generate_html(self, data: dict) -> str:
        """Gera um Dashboard unificado a partir do payload"""
        
        errors = data.get('errors', [])
        all_logs = data.get('logs', [])
        
        # Filtros para os contadores visuais
        critical_errors = [e for e in errors if e.get('diag', {}).get('severity') == 'CRITICAL']
        high_errors = [e for e in errors if e.get('diag', {}).get('severity') == 'HIGH']
        
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório Consolidado - {data.get('package', 'APK')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; padding: 20px; color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        
        /* Cabeçalho */
        .header {{ background: #1a237e; color: white; padding: 25px; border-radius: 8px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 24px; margin-bottom: 5px; }}
        .apk-badge {{ background: #3949ab; padding: 5px 15px; border-radius: 20px; font-size: 14px; border: 1px solid #5c6bc0; }}
        
        /* Stats */
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-box {{ background: #fff; border: 1px solid #e0e0e0; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .stat-box.danger {{ border-top: 4px solid #f44336; }}
        .stat-box.warning {{ border-top: 4px solid #ff9800; }}
        .stat-box.info {{ border-top: 4px solid #2196f3; }}
        .stat-box h3 {{ font-size: 36px; margin-bottom: 5px; color: #333; }}
        .stat-box p {{ color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
        
        /* Cards de Erro */
        .section-title {{ color: #1a237e; margin: 30px 0 15px 0; padding-bottom: 10px; border-bottom: 2px solid #e8eaf6; }}
        .error-card {{ background: #fff; border: 1px solid #e0e0e0; margin-bottom: 25px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .error-header {{ padding: 15px 20px; background: #fafafa; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; }}
        .error-header h3 {{ color: #d32f2f; font-size: 16px; }}
        .error-layer {{ background: #e0e0e0; color: #424242; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .error-body {{ padding: 20px; }}
        
        .action-box {{ background: #e3f2fd; border-left: 4px solid #1976d2; padding: 15px; margin: 15px 0; border-radius: 0 4px 4px 0; }}
        .action-box h4 {{ color: #0d47a1; margin-bottom: 5px; font-size: 14px; }}
        
        /* Logcat Console */
        .logcat-console {{ background: #2b2b2b; color: #a9b7c6; padding: 15px; font-family: 'Consolas', 'Monaco', monospace; font-size: 13px; overflow-x: auto; }}
        .logcat-title {{ color: #858585; margin-bottom: 10px; font-weight: bold; font-size: 12px; border-bottom: 1px solid #444; padding-bottom: 5px; letter-spacing: 1px; }}
        
        .empty-state {{ text-align: center; padding: 50px; color: #757575; background: #f5f5f5; border-radius: 8px; border: 1px dashed #bdbdbd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>Monitoramento de APK Completo</h1>
                <p style="color: #b8c1ec;">Timestamp: {data.get('timestamp')}</p>
            </div>
            <div>
                <span class="apk-badge">📦 {data.get('apk')} ({data.get('package')})</span>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-box info">
                <h3>{len(all_logs)}</h3>
                <p>Logs Capturados</p>
            </div>
            <div class="stat-box warning">
                <h3>{len(errors)}</h3>
                <p>Total de Erros</p>
            </div>
            <div class="stat-box danger">
                <h3 style="color: #f44336;">{len(critical_errors) + len(high_errors)}</h3>
                <p>Erros Severos</p>
            </div>
        </div>
        
        <h2 class="section-title">🚨 Registro Detalhado de Erros</h2>
"""
        
        if errors:
            for error_item in errors:
                diag = error_item.get('diag', {})
                log = error_item.get('log', {})
                layer = diag.get('layer', 'UNKNOWN')
                
                html += f"""
            <div class="error-card">
                <div class="error-header">
                    <h3>{diag.get('error_type', 'Erro Detectado')} - {log.get('timestamp', '')}</h3>
                    <span class="error-layer">{layer}</span>
                </div>
                
                <div class="error-body">
                    <p><strong>Causa Raiz:</strong> {diag.get('root_cause', 'N/A')}</p>
                    
                    <div class="action-box">
                        <h4>🔧 AÇÃO RECOMENDADA ({diag.get('responsible_team', 'GERAL')}):</h4>
                        <p>{str(diag.get('recommended_action', 'Analisar o contexto do erro abaixo.')).replace(chr(10), '<br>')}</p>
                    </div>
                </div>
                
                <div class="logcat-console">
                    <div class="logcat-title">>_ CONTEXTO DO LOGCAT (PID: {log.get('pid', 'N/A')})</div>
                    {self._get_log_context_html(all_logs, log, context_size=6)}
                </div>
            </div>
"""
        else:
            html += """
            <div class="empty-state">
                <h3 style="margin-bottom: 10px; color: #4caf50;">✅ Tudo certo!</h3>
                <p>Nenhum erro foi capturado durante a sessão de monitoramento.</p>
            </div>
"""
            
        html += """
    </div>
</body>
</html>
"""
        return html