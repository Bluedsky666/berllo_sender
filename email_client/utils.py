import json
import csv
import re

def is_valid_email(email: str) -> bool:
    """
    使用一个更严格的正则表达式来验证邮箱格式。
    这个规则不允许邮箱的用户名部分以点或连字符开头或结尾。
    """
    if not email:
        return False
    # 更新后的、更严格的邮箱格式正则表达式
    pattern = re.compile(
        r"^(?=[a-zA-Z0-9@._%+-]{6,254}$)[a-zA-Z0-9._%+-]{1,64}@"
        r"(?:[a-zA-Z0-9-]{1,63}\.){1,8}[a-zA-Z]{2,63}$"
    )
    # 辅助规则，检查开头和结尾的特殊字符
    if email.startswith('.') or email.endswith('.') or email.startswith('-') or email.endswith('-'):
        return False
    if '..' in email or '--' in email or '.-' in email or '-.' in email:
        return False

    return pattern.match(email) is not None

def load_emails_from_file(filepath: str):
    """
    从文件中加载邮件列表。
    支持 TXT, JSON, 和 CSV 格式。
    加载时会自动进行小写转换和去重，并过滤无效格式。
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
                    # 兼容可能存在的列名带空格的情况
                    email_val = next((row[k] for k in row if k.strip().lower() == 'email'), "").strip()
                    if is_valid_email(email_val):
                        unique_emails.add(email_val.lower())
        except FileNotFoundError:
            raise ValueError(f"文件未找到: {filepath}")
    else:
        raise ValueError("不支持的文件格式。请使用 .txt, .json 或 .csv。")

    return [{"email": email} for email in sorted(list(unique_emails))]
