import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import re
import configparser
import os
from api import ApiClient
from utils import load_emails_from_file

CONFIG_FILE = 'config.ini'

class EmailClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("伯勒邮件群发器 - API客户端")
        self.root.geometry("800x700")

        self.email_list = []
        self.api_client = None
        self.config = configparser.ConfigParser()

        self.create_config_frame()
        self.load_config()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.send_tab = ttk.Frame(self.notebook, padding="10")
        self.push_tab = ttk.Frame(self.notebook, padding="10")
        self.query_tab = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.send_tab, text="批量发送")
        self.notebook.add(self.push_tab, text="单封推送")
        self.notebook.add(self.query_tab, text="结果查询")

        self.create_send_tab_widgets()
        self.create_push_tab_widgets()
        self.create_query_tab_widgets()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        if not os.path.exists(CONFIG_FILE): return
        self.config.read(CONFIG_FILE)
        if 'API' in self.config:
            api_config = self.config['API']
            self.host_var.set(api_config.get('Host', '127.0.0.1'))
            self.port_var.set(api_config.get('Port', '8060'))
            self.key_var.set(api_config.get('Key', ''))

    def save_config(self):
        self.config['API'] = {'Host': self.host_var.get(), 'Port': self.port_var.get(), 'Key': self.key_var.get()}
        with open(CONFIG_FILE, 'w') as configfile: self.config.write(configfile)

    def on_closing(self):
        self.save_config()
        self.root.destroy()

    def create_config_frame(self):
        config_frame = ttk.LabelFrame(self.root, text="API 配置", padding="10")
        config_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(config_frame, text="主机:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.host_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(config_frame, textvariable=self.host_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(config_frame, text="端口:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.port_var = tk.StringVar(value="8060")
        ttk.Entry(config_frame, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(config_frame, text="密钥 (可选):").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.key_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.key_var, width=30, show="*").grid(row=0, column=5, padx=5, pady=5, sticky="we")
        self.test_button = ttk.Button(config_frame, text="测试连接", command=self.test_api_connection)
        self.test_button.grid(row=0, column=6, padx=10, pady=5)
        self.status_label = ttk.Label(config_frame, text="请先配置并测试连接", foreground="blue")
        self.status_label.grid(row=0, column=7, padx=5, pady=5, sticky="w")
        config_frame.columnconfigure(5, weight=1)

    def _test_api_connection_thread(self):
        try:
            host = self.host_var.get(); port = int(self.port_var.get()); key = self.key_var.get()
            self.api_client = ApiClient(host=host, port=port, key=key)
            result = self.api_client.test_connection()
            if result and result.get("ret") == 200:
                self.status_label.config(text="连接成功: " + result.get("msg", "OK"), foreground="green")
                self.save_config()
            else:
                self.status_label.config(text="连接失败: " + result.get("msg", "未知错误"), foreground="red")
        except Exception as e:
            self.status_label.config(text=f"连接失败: {e}", foreground="red")
        finally:
            self.root.after(0, self.test_button.config, {"state": "normal"})

    def create_push_tab_widgets(self):
        canvas = tk.Canvas(self.push_tab); scrollbar = ttk.Scrollbar(self.push_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        fields = {"email": "收件人邮箱:", "subject": "邮件标题:", "def1": "宏定义1:", "def2": "宏定义2:", "def3": "宏定义3:", "def4": "宏定义4:", "def5": "宏定义5:"}
        self.push_vars = {}
        for i, (key, text) in enumerate(fields.items()):
            ttk.Label(scrollable_frame, text=text).grid(row=i, column=0, padx=5, pady=5, sticky='w')
            var = tk.StringVar(); self.push_vars[key] = var
            ttk.Entry(scrollable_frame, textvariable=var, width=80).grid(row=i, column=1, padx=5, pady=5, sticky='we')
        ttk.Label(scrollable_frame, text="邮件内容:").grid(row=len(fields), column=0, padx=5, pady=5, sticky='nw')
        self.push_content_text = tk.Text(scrollable_frame, height=10, width=80)
        self.push_content_text.grid(row=len(fields), column=1, padx=5, pady=5, sticky='we')
        scrollable_frame.columnconfigure(1, weight=1)
        self.push_button = ttk.Button(scrollable_frame, text="立即推送", command=self.start_push_send)
        self.push_button.grid(row=len(fields) + 1, column=1, pady=10, sticky='e')
        ttk.Label(scrollable_frame, text="结果ID:").grid(row=len(fields) + 2, column=0, padx=5, pady=5, sticky='w')
        self.push_result_id_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.push_result_id_var, state='readonly', width=80).grid(row=len(fields) + 2, column=1, padx=5, pady=5, sticky='we')

    def _bulk_send_thread(self):
        total_emails = len(self.email_list)
        self.root.after(0, self.progress_bar.config, {"maximum": total_emails, "value": 0})
        # 初始化状态显示
        initial_status_text = f"成功: 0 | 失败: 0 | 总计: {total_emails}"
        self.root.after(0, self.status_summary_label.config, {"text": initial_status_text})

        try:
            tid = self.tid_var.get(); tid = int(tid) if tid.isdigit() else None
            send_response = self.api_client.send_bulk_emails(self.email_list, template_id=tid)
            if send_response.get("ret") != 200: raise Exception(f"API提交失败: {send_response.get('msg', '未知错误')}")

            email_ids = send_response.get("data", {}).get("email_id", [])
            guids_to_query = [item.split('_')[1] for item in email_ids if '_' in item]

            results = {} # guid -> status_code
            success_count, failure_count = 0, 0
            start_time = time.time()

            while len(results) < len(guids_to_query):
                time.sleep(5)
                pending_guids = [g for g in guids_to_query if g not in results]
                if not pending_guids: break

                query_response = self.api_client.query_send_results(pending_guids)
                if query_response.get("ret") == 200 and "data" in query_response and "result" in query_response["data"]:
                    for res_str in query_response["data"]["result"]:
                        try:
                            guid, status_part = res_str.split('_', 1)
                            if guid not in results:
                                status_code = status_part.split('|', 1)[0]
                                results[guid] = status_code
                                if status_code == '2':
                                    success_count += 1
                                else:
                                    failure_count += 1
                        except (ValueError, IndexError):
                            continue

                processed_count = success_count + failure_count
                eta_str = ""
                if processed_count > 0:
                    elapsed_time = time.time() - start_time
                    time_per_email = elapsed_time / processed_count
                    remaining_emails = total_emails - processed_count
                    eta = time_per_email * remaining_emails
                    eta_str = f" | ETA: {time.strftime('%H:%M:%S', time.gmtime(eta))}"

                # 更新UI
                status_text = f"成功: {success_count} | 失败: {failure_count} | 总计: {total_emails}{eta_str}"
                self.root.after(0, self.progress_bar.config, {"value": processed_count})
                self.root.after(0, self.status_summary_label.config, {"text": status_text})

            self.root.after(0, messagebox.showinfo, "发送完成", f"全部 {total_emails} 封邮件已处理完毕。\n成功: {success_count}\n失败: {failure_count}")

        except Exception as e:
            self.root.after(0, messagebox.showerror, "发送出错", str(e))
        finally:
            self.root.after(0, self.send_button.config, {"state": "normal"})

    # --- Other methods are collapsed for brevity ---
    def test_api_connection(self):
        self.test_button.config(state="disabled")
        self.status_label.config(text="正在测试...", foreground="orange")
        thread = threading.Thread(target=self._test_api_connection_thread)
        thread.daemon = True
        thread.start()

    def create_send_tab_widgets(self):
        top_frame = ttk.Frame(self.send_tab)
        top_frame.pack(fill='x', pady=5)
        ttk.Button(top_frame, text="加载邮件文件", command=self.load_email_file).pack(side='left')
        ttk.Label(top_frame, text="模板ID (可选):").pack(side='left', padx=(10, 0))
        self.tid_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.tid_var, width=10).pack(side='left', padx=5)
        self.send_button = ttk.Button(top_frame, text="开始发送", command=self.start_bulk_send)
        self.send_button.pack(side='left', padx=10)
        tree_frame = ttk.Frame(self.send_tab)
        tree_frame.pack(expand=True, fill='both', pady=5)
        self.email_tree = ttk.Treeview(tree_frame, columns=("email",), show='headings')
        self.email_tree.heading("email", text="邮箱地址")
        self.email_tree.pack(side='left', expand=True, fill='both')
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.email_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.email_tree.configure(yscrollcommand=scrollbar.set)
        bottom_frame = ttk.Frame(self.send_tab)
        bottom_frame.pack(fill='x', pady=5)
        self.progress_label = ttk.Label(bottom_frame, text="进度:")
        self.progress_label.pack(side='left')
        self.progress_bar = ttk.Progressbar(bottom_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(side='left', expand=True, fill='x', padx=5)
        self.status_summary_label = ttk.Label(bottom_frame, text="未开始")
        self.status_summary_label.pack(side='left')

    def load_email_file(self):
        filepath = filedialog.askopenfilename(title="请选择邮件文件", filetypes=(("文本文件", "*.txt"), ("CSV 文件", "*.csv"), ("JSON 文件", "*.json"), ("所有文件", "*.*")))
        if not filepath: return
        try:
            self.email_list = load_emails_from_file(filepath)
            self.populate_email_treeview()
            messagebox.showinfo("加载成功", f"成功加载 {len(self.email_list)} 个有效且唯一的邮箱地址。")
        except Exception as e:
            messagebox.showerror("加载失败", f"加载文件时出错: {e}")

    def populate_email_treeview(self):
        for item in self.email_tree.get_children(): self.email_tree.delete(item)
        if not self.email_list: return
        headers = list(self.email_list[0].keys())
        self.email_tree["columns"] = headers
        for header in headers:
            self.email_tree.heading(header, text=header)
            self.email_tree.column(header, width=150)
        for email_data in self.email_list:
            values = [email_data.get(h, "") for h in headers]
            self.email_tree.insert("", "end", values=values)

    def start_bulk_send(self):
        if not self.email_list: messagebox.showwarning("无法发送", "请先加载邮件文件。"); return
        if not self.api_client: messagebox.showwarning("无法发送", "请先成功测试API连接。"); return
        self.send_button.config(state="disabled")
        thread = threading.Thread(target=self._bulk_send_thread)
        thread.daemon = True
        thread.start()

    def start_push_send(self):
        if not self.push_vars['email'].get() or not self.push_vars['subject'].get(): messagebox.showwarning("信息不完整", "收件人邮箱和邮件标题不能为空。"); return
        if not self.api_client: messagebox.showwarning("无法发送", "请先成功测试API连接。"); return
        self.push_button.config(state="disabled")
        thread = threading.Thread(target=self._push_send_thread)
        thread.daemon = True
        thread.start()

    def _push_send_thread(self):
        try:
            data = {key: var.get() for key, var in self.push_vars.items()}
            data['content'] = self.push_content_text.get("1.0", "end-1c")
            result = self.api_client.push_single_email(email=data['email'], subject=data['subject'], content=data['content'], def1=data['def1'], def2=data['def2'], def3=data['def3'], def4=data['def4'], def5=data['def5'])
            if result and result.get("ret") == 200:
                email_id = result.get("data", {}).get("email_id", "N/A")
                self.root.after(0, self.push_result_id_var.set, email_id)
                self.root.after(0, messagebox.showinfo, "推送成功", "邮件已成功推送！")
            else:
                msg = result.get("msg", "未知错误")
                self.root.after(0, messagebox.showerror, "推送失败", f"错误: {msg}")
        except Exception as e:
            self.root.after(0, messagebox.showerror, "推送出错", str(e))
        finally:
            self.root.after(0, self.push_button.config, {"state": "normal"})

    def create_query_tab_widgets(self):
        top_frame = ttk.Frame(self.query_tab); top_frame.pack(fill='x', pady=5)
        ttk.Label(top_frame, text="输入要查询的GUID (每行一个):").pack(side='left')
        self.query_button = ttk.Button(top_frame, text="查询状态", command=self.start_query_results)
        self.query_button.pack(side='right', padx=10)
        text_frame = ttk.Frame(self.query_tab); text_frame.pack(expand=True, fill='both', pady=5)
        self.query_text = tk.Text(text_frame, height=10, width=80)
        self.query_text.pack(side='left', expand=True, fill='both')
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.query_text.yview)
        text_scrollbar.pack(side='right', fill='y'); self.query_text.configure(yscrollcommand=text_scrollbar.set)
        ttk.Label(self.query_tab, text="查询结果:").pack(fill='x', pady=(10, 0))
        result_frame = ttk.Frame(self.query_tab); result_frame.pack(expand=True, fill='both', pady=5)
        self.query_tree = ttk.Treeview(result_frame, columns=("guid", "status"), show='headings')
        self.query_tree.heading("guid", text="GUID"); self.query_tree.heading("status", text="状态")
        self.query_tree.column("guid", width=300); self.query_tree.column("status", width=400)
        self.query_tree.pack(side='left', expand=True, fill='both')
        result_scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.query_tree.yview)
        result_scrollbar.pack(side='right', fill='y'); self.query_tree.configure(yscrollcommand=result_scrollbar.set)

    def start_query_results(self):
        guids_str = self.query_text.get("1.0", "end-1c").strip()
        if not guids_str: messagebox.showwarning("信息不完整", "请输入至少一个GUID进行查询。"); return
        if not self.api_client: messagebox.showwarning("无法查询", "请先成功测试API连接。"); return
        self.query_button.config(state="disabled")
        thread = threading.Thread(target=self._query_results_thread, args=(guids_str,))
        thread.daemon = True
        thread.start()

    def _query_results_thread(self, guids_str):
        try:
            guids = [line.strip() for line in guids_str.splitlines() if line.strip()]
            if not guids: raise ValueError("未提供有效的GUID。")
            result = self.api_client.query_send_results(guids)
            if result and result.get("ret") == 200:
                results__data = result.get("data", {}).get("result", [])
                self.root.after(0, self.populate_query_tree, results_data)
            else:
                msg = result.get("msg", "未知错误")
                self.root.after(0, messagebox.showerror, "查询失败", f"错误: {msg}")
        except Exception as e:
            self.root.after(0, messagebox.showerror, "查询出错", str(e))
        finally:
            self.root.after(0, self.query_button.config, {"state": "normal"})

    def populate_query_tree(self, results_data):
        for item in self.query_tree.get_children(): self.query_tree.delete(item)
        for res_str in results_data:
            try:
                guid, status = res_str.split('_', 1)
                status = status.replace('|', ': ', 1)
            except ValueError:
                guid = res_str; status = "格式无法解析"
            self.query_tree.insert("", "end", values=(guid, status))

if __name__ == "__main__":
    root = tk.Tk()
    app = EmailClientGUI(root)
    root.mainloop()
