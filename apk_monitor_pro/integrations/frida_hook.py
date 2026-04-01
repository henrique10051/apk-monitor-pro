"""
Frida Integration - Hooking dinâmico de métodos
Intercepta chamadas de métodos Java em tempo real
"""

import subprocess
import json
from typing import Callable, Optional, List, Dict


class FridaHooker:
    """
    Integração com Frida para hooking de métodos
    
    Permite interceptar:
    - Chamadas de sincronização
    - Queries SQLite
    - Chamadas HTTP
    - Métodos customizados
    """
    
    def __init__(self, package_name: str):
        self.package_name = package_name
        self.session = None
        self.script = None
        self.hooks_active = []
        
    def check_frida_available(self) -> bool:
        """Verifica se Frida está instalado"""
        try:
            result = subprocess.run(
                ["frida", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def check_frida_server(self) -> bool:
        """Verifica se frida-server está rodando no dispositivo"""
        try:
            result = subprocess.run(
                ["adb", "shell", "ps", "|", "grep", "frida-server"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            return 'frida-server' in result.stdout
        except:
            return False
    
    def start_frida_server(self) -> bool:
        """
        Inicia frida-server no dispositivo (requer setup prévio)
        
        Returns:
            True se iniciou com sucesso
        """
        try:
            # Locais comuns onde frida-server pode estar
            possible_locations = [
                "/data/local/tmp/frida-server",
                "/data/local/tmp/frida-server-16.0.0-android-arm64",
                "/data/local/tmp/frida-server-16.0.0-android-arm",
                "/data/local/tmp/frida-server-15.2.2-android-arm64",
                "/data/local/tmp/frida-server-15.2.2-android-arm"
            ]
            
            frida_path = None
            
            # Procura qual existe
            for path in possible_locations:
                result = subprocess.run(
                    ["adb", "shell", "su", "-c", f"ls {path}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and path in result.stdout:
                    frida_path = path
                    print(f"✅ Frida encontrado em: {frida_path}")
                    break
            
            if not frida_path:
                print("❌ Frida-server não encontrado em nenhum local comum")
                print("   Baixe de: https://github.com/frida/frida/releases")
                print("   Execute: adb push frida-server /data/local/tmp/")
                return False
            
            # Garante permissão de execução
            subprocess.run(
                ["adb", "shell", "su", "-c", f"chmod 755 {frida_path}"],
                capture_output=True,
                timeout=5
            )
            
            # Mata processos antigos
            subprocess.run(
                ["adb", "shell", "su", "-c", "killall frida-server"],
                capture_output=True,
                timeout=5
            )
            
            import time
            time.sleep(1)
            
            # Inicia em background
            subprocess.Popen(
                ["adb", "shell", "su", "-c", f"{frida_path} &"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Aguarda iniciar
            time.sleep(2)
            
            # Verifica se está rodando
            return self.check_frida_server()
            
        except Exception as e:
            print(f"Erro ao iniciar frida-server: {e}")
            return False
    
    def hook_sync_methods(self, callback: Callable) -> bool:
        """
        Hook em métodos de sincronização
        
        Args:
            callback: Função chamada quando método é interceptado
            
        Returns:
            True se hook foi instalado
        """
        try:
            import frida
            
            # Conecta ao app
            device = frida.get_usb_device()
            pid = device.spawn([self.package_name])
            self.session = device.attach(pid)
            device.resume(pid)
            
            # Script Frida para hookar métodos de sync
            script_code = """
            Java.perform(function() {
                // Procura classes de sincronização
                var classes = Java.enumerateLoadedClassesSync();
                
                classes.forEach(function(className) {
                    if (className.indexOf('Sync') !== -1 || 
                        className.indexOf('sync') !== -1) {
                        
                        try {
                            var SyncClass = Java.use(className);
                            
                            // Hook em todos os métodos
                            var methods = SyncClass.class.getDeclaredMethods();
                            methods.forEach(function(method) {
                                var methodName = method.getName();
                                
                                if (methodName !== 'constructor') {
                                    SyncClass[methodName].overload().implementation = function() {
                                        var args = Array.prototype.slice.call(arguments);
                                        
                                        send({
                                            type: 'sync_call',
                                            class: className,
                                            method: methodName,
                                            arguments: args.map(String),
                                            timestamp: new Date().toISOString()
                                        });
                                        
                                        var result = this[methodName].apply(this, arguments);
                                        
                                        send({
                                            type: 'sync_return',
                                            class: className,
                                            method: methodName,
                                            result: String(result),
                                            timestamp: new Date().toISOString()
                                        });
                                        
                                        return result;
                                    };
                                }
                            });
                        } catch(e) {
                            // Ignora erros
                        }
                    }
                });
            });
            """
            
            self.script = self.session.create_script(script_code)
            self.script.on('message', lambda message, data: callback(message))
            self.script.load()
            
            self.hooks_active.append('sync_methods')
            
            return True
            
        except Exception as e:
            print(f"Erro ao instalar hook de sync: {e}")
            return False
    
    def hook_sqlite_queries(self, callback: Callable) -> bool:
        """
        Hook em queries SQLite
        
        Args:
            callback: Função chamada quando query é executada
            
        Returns:
            True se hook foi instalado
        """
        try:
            import frida
            
            if not self.session:
                device = frida.get_usb_device()
                pid = device.spawn([self.package_name])
                self.session = device.attach(pid)
                device.resume(pid)
            
            # Script para hookar SQLite
            script_code = """
            Java.perform(function() {
                var SQLiteDatabase = Java.use('android.database.sqlite.SQLiteDatabase');
                
                // Hook execSQL
                SQLiteDatabase.execSQL.overload('java.lang.String').implementation = function(sql) {
                    send({
                        type: 'sqlite_query',
                        operation: 'execSQL',
                        query: sql,
                        timestamp: new Date().toISOString()
                    });
                    
                    return this.execSQL(sql);
                };
                
                // Hook rawQuery
                SQLiteDatabase.rawQuery.overload('java.lang.String', '[Ljava.lang.String;').implementation = function(sql, args) {
                    send({
                        type: 'sqlite_query',
                        operation: 'rawQuery',
                        query: sql,
                        arguments: args ? Java.array('java.lang.String', args) : [],
                        timestamp: new Date().toISOString()
                    });
                    
                    return this.rawQuery(sql, args);
                };
                
                // Hook insert
                SQLiteDatabase.insert.overload('java.lang.String', 'java.lang.String', 'android.content.ContentValues').implementation = function(table, nullColumnHack, values) {
                    send({
                        type: 'sqlite_query',
                        operation: 'INSERT',
                        table: table,
                        values: String(values),
                        timestamp: new Date().toISOString()
                    });
                    
                    return this.insert(table, nullColumnHack, values);
                };
                
                // Hook update
                SQLiteDatabase.update.overload('java.lang.String', 'android.content.ContentValues', 'java.lang.String', '[Ljava.lang.String;').implementation = function(table, values, whereClause, whereArgs) {
                    send({
                        type: 'sqlite_query',
                        operation: 'UPDATE',
                        table: table,
                        values: String(values),
                        where: whereClause,
                        timestamp: new Date().toISOString()
                    });
                    
                    return this.update(table, values, whereClause, whereArgs);
                };
                
                // Hook delete
                SQLiteDatabase.delete.overload('java.lang.String', 'java.lang.String', '[Ljava.lang.String;').implementation = function(table, whereClause, whereArgs) {
                    send({
                        type: 'sqlite_query',
                        operation: 'DELETE',
                        table: table,
                        where: whereClause,
                        timestamp: new Date().toISOString()
                    });
                    
                    return this.delete(table, whereClause, whereArgs);
                };
            });
            """
            
            script = self.session.create_script(script_code)
            script.on('message', lambda message, data: callback(message))
            script.load()
            
            self.hooks_active.append('sqlite_queries')
            
            return True
            
        except Exception as e:
            print(f"Erro ao instalar hook SQLite: {e}")
            return False
    
    def hook_http_requests(self, callback: Callable) -> bool:
        """
        Hook em requisições HTTP/HTTPS
        
        Args:
            callback: Função chamada quando request é feito
            
        Returns:
            True se hook foi instalado
        """
        try:
            import frida
            
            if not self.session:
                device = frida.get_usb_device()
                pid = device.spawn([self.package_name])
                self.session = device.attach(pid)
                device.resume(pid)
            
            # Script para hookar HTTP
            script_code = """
            Java.perform(function() {
                // Hook OkHttp (popular lib)
                try {
                    var OkHttpClient = Java.use('okhttp3.OkHttpClient');
                    var Request = Java.use('okhttp3.Request');
                    
                    OkHttpClient.newCall.implementation = function(request) {
                        var url = request.url().toString();
                        var method = request.method();
                        
                        send({
                            type: 'http_request',
                            library: 'OkHttp',
                            method: method,
                            url: url,
                            timestamp: new Date().toISOString()
                        });
                        
                        return this.newCall(request);
                    };
                } catch(e) {}
                
                // Hook HttpURLConnection (Android nativo)
                try {
                    var HttpURLConnection = Java.use('java.net.HttpURLConnection');
                    
                    HttpURLConnection.connect.implementation = function() {
                        var url = this.getURL().toString();
                        var method = this.getRequestMethod();
                        
                        send({
                            type: 'http_request',
                            library: 'HttpURLConnection',
                            method: method,
                            url: url,
                            timestamp: new Date().toISOString()
                        });
                        
                        return this.connect();
                    };
                } catch(e) {}
            });
            """
            
            script = self.session.create_script(script_code)
            script.on('message', lambda message, data: callback(message))
            script.load()
            
            self.hooks_active.append('http_requests')
            
            return True
            
        except Exception as e:
            print(f"Erro ao instalar hook HTTP: {e}")
            return False
    
    def hook_custom_method(self, class_name: str, method_name: str, 
                          callback: Callable) -> bool:
        """
        Hook em método específico customizado
        
        Args:
            class_name: Nome completo da classe (ex: com.overit.app.MainActivity)
            method_name: Nome do método
            callback: Função de callback
            
        Returns:
            True se hook foi instalado
        """
        try:
            import frida
            
            if not self.session:
                device = frida.get_usb_device()
                pid = device.spawn([self.package_name])
                self.session = device.attach(pid)
                device.resume(pid)
            
            # Script customizado
            script_code = f"""
            Java.perform(function() {{
                var TargetClass = Java.use('{class_name}');
                
                TargetClass.{method_name}.implementation = function() {{
                    var args = Array.prototype.slice.call(arguments);
                    
                    send({{
                        type: 'custom_method_call',
                        class: '{class_name}',
                        method: '{method_name}',
                        arguments: args.map(String),
                        timestamp: new Date().toISOString()
                    }});
                    
                    var result = this.{method_name}.apply(this, arguments);
                    
                    send({{
                        type: 'custom_method_return',
                        class: '{class_name}',
                        method: '{method_name}',
                        result: String(result),
                        timestamp: new Date().toISOString()
                    }});
                    
                    return result;
                }};
            }});
            """
            
            script = self.session.create_script(script_code)
            script.on('message', lambda message, data: callback(message))
            script.load()
            
            self.hooks_active.append(f'custom_{class_name}.{method_name}')
            
            return True
            
        except Exception as e:
            print(f"Erro ao instalar hook customizado: {e}")
            return False
    
    def get_loaded_classes(self) -> List[str]:
        """
        Lista todas as classes carregadas na APK
        
        Returns:
            Lista de nomes de classes
        """
        try:
            import frida
            
            if not self.session:
                device = frida.get_usb_device()
                pid = device.spawn([self.package_name])
                self.session = device.attach(pid)
                device.resume(pid)
            
            script_code = """
            Java.perform(function() {
                var classes = Java.enumerateLoadedClassesSync();
                send({type: 'classes', data: classes});
            });
            """
            
            classes = []
            
            def on_message(message, data):
                if message['type'] == 'send':
                    payload = message['payload']
                    if payload['type'] == 'classes':
                        classes.extend(payload['data'])
            
            script = self.session.create_script(script_code)
            script.on('message', on_message)
            script.load()
            
            import time
            time.sleep(1)
            
            return classes
            
        except Exception as e:
            print(f"Erro ao listar classes: {e}")
            return []
    
    def cleanup(self):
        """Limpa recursos Frida"""
        if self.script:
            self.script.unload()
        if self.session:
            self.session.detach()
        
        self.hooks_active.clear()


# Guia de Setup do Frida
FRIDA_SETUP_GUIDE = """
═══════════════════════════════════════════════════════════════
                    SETUP DO FRIDA
═══════════════════════════════════════════════════════════════

O Frida permite hooking avançado de métodos em tempo real.

📋 REQUISITOS:
1. Dispositivo Android com ROOT
2. frida-tools instalado no PC
3. frida-server rodando no dispositivo

🔧 INSTALAÇÃO:

1️⃣ Instalar frida-tools no PC:
   pip install frida frida-tools

2️⃣ Baixar frida-server para Android:
   a) Vá em: https://github.com/frida/frida/releases
   b) Baixe versão correta (ex: frida-server-16.0.0-android-arm64.xz)
   c) Extraia o arquivo

3️⃣ Instalar frida-server no dispositivo:
   # Enviar para dispositivo
   adb push frida-server /data/local/tmp/
   
   # Dar permissão
   adb shell "su -c chmod 755 /data/local/tmp/frida-server"
   
   # Executar
   adb shell "su -c /data/local/tmp/frida-server &"

4️⃣ Verificar se está rodando:
   frida-ps -U

   Deve listar processos do dispositivo!

✅ PRONTO! Agora você pode usar hooking avançado!

═══════════════════════════════════════════════════════════════

💡 CASOS DE USO:

1. Ver TODAS as chamadas de sincronização:
   - Intercepta quando sync() é chamado
   - Vê parâmetros passados
   - Vê retorno do método

2. Ver TODAS as queries SQLite:
   - Intercepta INSERT, UPDATE, DELETE, SELECT
   - Vê tabelas acessadas
   - Vê tempo de execução

3. Ver TODAS as chamadas HTTP:
   - Intercepta antes de enviar request
   - Vê URL, método, headers, body
   - Vê response

4. Hookar métodos específicos:
   - Qualquer método Java pode ser interceptado
   - Útil para debug de lógica específica

═══════════════════════════════════════════════════════════════
"""