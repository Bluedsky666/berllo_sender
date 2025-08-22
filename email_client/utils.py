import json
import csv
import re

def is_valid_email(email: str) -> bool:
    """
    使用一个简单的正则表达式来验证邮箱格式。
    """
    if not email:
        return False
    # 一个相对宽松但常用的邮箱格式正则表达式
    pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    return pattern.match(email) is not None

def load_emails_from_file(filepath: str):
    """
    从文件中加载邮件列表。
    支持 TXT, JSON, 和 CSV 格式。
    加载时会自动进行小写转换和去重。
    """
    if not filepath:
        raise ValueError("未提供文件路径。")

    unique_emails = set()

    if filepath.lower().endswith('.txt'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    email = line.strip()
                    if is_valid_email(email):
                        unique_emails.add(email.lower())
        except FileNotFoundError:
            raise ValueError(f"文件未找到: {filepath}")

    elif filepath.lower().endswith('.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON 文件必须包含一个邮件对象的列表。")

            for item in data:
                email = item.get("email", "").strip()
                if is_valid_email(email):
                    # 为了保持一致性，即使是JSON/CSV，也只取email并去重
                    unique_emails.add(email.lower())

        except json.JSONDecodeError:
            raise ValueError("无效的 JSON 格式。")
        except FileNotFoundError:
            raise ValueError(f"文件未找到: {filepath}")

    elif filepath.lower().endswith('.csv'):
        try:
            with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                fieldnames = [field.strip().lower() for field in reader.fieldnames]
                if 'email' not in fieldnames:
                    raise ValueError("CSV 文件必须包含一个 'email' 列。")

                for row in reader:
                    email = row.get("email", "").strip()
                    if is_valid_email(email):
                        unique_emails.add(email.lower())
        except FileNotFoundError:
            raise ValueError(f"文件未找到: {filepath}")
    else:
        raise ValueError("不支持的文件格式。请使用 .txt, .json 或 .csv。")

    # 将去重后的email集合转换为API所需的字典列表格式
    # 注意：由于TXT格式没有宏，为了统一，我们现在只处理email字段。
    # 如果未来需要支持从CSV/JSON加载宏，这里的逻辑需要调整。
    # 当前根据用户最新需求，统一为只加载和处理email。
    return [{"email": email} for email in sorted(list(unique_emails))]
