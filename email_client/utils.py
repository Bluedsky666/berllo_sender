import json
import csv

def load_emails_from_file(filepath: str):
    """
    从文件中加载邮件列表。
    支持 JSON 和 CSV 格式。

    对于 JSON，文件应包含一个对象列表，每个对象都有一个 "email" 键
    和可选的 "def1" 到 "def5" 键。
    例如: [{"email": "test@example.com", "def1": "value1"}]

    对于 CSV，文件应有标题行。
    标题必须包含 "email"。可选的标题是 "def1" 到 "def5"。
    例如:
    email,def1,def2
    test@example.com,val1,val2

    返回一个字典列表，如果格式无效则引发错误。
    """
    if filepath.lower().endswith('.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON 文件必须包含一个邮件对象的列表。")
            return data
        except json.JSONDecodeError:
            raise ValueError("无效的 JSON 格式。")
        except FileNotFoundError:
            raise ValueError(f"文件未找到: {filepath}")

    elif filepath.lower().endswith('.csv'):
        try:
            # 使用 'utf-8-sig' 来处理可能由Excel等软件在文件开头添加的BOM
            with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
                # 使用 DictReader 直接将行转换为字典
                reader = csv.DictReader(f)

                # 清理并验证 'email' 列是否存在
                fieldnames = [field.strip() for field in reader.fieldnames]
                if 'email' not in fieldnames:
                    raise ValueError("CSV 文件必须包含一个 'email' 列。")

                # 清理每行数据中键名可能带有的空格
                data = []
                for row in reader:
                    data.append({key.strip(): value for key, value in row.items()})
                return data
        except FileNotFoundError:
            raise ValueError(f"文件未找到: {filepath}")
    else:
        raise ValueError("不支持的文件格式。请使用 .json 或 .csv。")
