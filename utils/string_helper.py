import json
import random
import re
import string
import uuid


def extract_number_with_unit(
    text: str, convert_unit: bool = True, unit_type: str = "default"
) -> float:
    """
    从带单位的数值文本中提取数值，支持万、亿、百分比等单位

    Args:
        text: 带单位的数值文本，如"3.964亿份"、"1.2万元"、"5.5亿美元"、"0.60%"等
        convert_unit: 是否转换单位为基本单位。默认为True
                     True时："3.964亿" -> 396400000.0, "0.60%" -> 0.6
                     False时："3.964亿" -> 3.964, "0.60%" -> 60.0
        unit_type: 指定单位类型，可选值:
                  'default' - 自动检测单位(万、亿)
                  'percentage' - 百分比单位

    Returns:
        float: 提取出的数值。如果无法提取则返回0.0

    Examples:
        >>> extract_number_with_unit("3.964亿份")
        396400000.0
        >>> extract_number_with_unit("1.2万元")
        12000.0
        >>> extract_number_with_unit("5.5亿美元", convert_unit=False)
        5.5
        >>> extract_number_with_unit("0.60%", unit_type='percentage')
        0.006
        >>> extract_number_with_unit("0.60%", unit_type='percentage', convert_unit=False)
        0.6
        >>> extract_number_with_unit("无效文本")
        0.0
    """
    try:
        # 处理百分比
        if unit_type == "percentage":
            number = float(text.split("%")[0].strip())
            return number / 100 if convert_unit else number

        # 处理其他单位

        match = re.search(r"([\d.]+)([万亿])?", text)
        if not match:
            return 0.0

        number = float(match.group(1))
        unit = match.group(2) if match.group(2) else ""

        # 处理单位转换
        if unit == "亿":
            return number * 100000000 if convert_unit else number
        if unit == "万":
            return number * 10000 if convert_unit else number
        return number

    except (ValueError, IndexError, AttributeError):
        return 0.0


def generate_random_string(length=20, chars=string.digits):
    """
    生成指定长度的随机字符串
    :param length: 长度
    :param chars: 字符集
    :return: 随机字符串
    """
    return "".join(random.choice(chars) for _ in range(length))


def get_json_from_jsonp_simple(jsonp_str):
    """
    从jsonp格式文本中解析json对象
    快速方法，仅支持：jsonp({"key": "value"})
    """
    # 找到第一个'('和最后一个')'
    start = jsonp_str.find("(") + 1
    end = jsonp_str.rfind(")")

    if 0 < start < end:
        json_str = jsonp_str[start:end]
        return json.loads(json_str)
    return None


def get_uuid():
    """生成UUID"""
    return str(uuid.uuid4())


def json_str_to_dict(data: str) -> dict:
    """将数据转换为dict"""
    try:
        if isinstance(data, str):
            return json.loads(data)
    except json.JSONDecodeError:
        return {"error": "无法解析的参数"}
