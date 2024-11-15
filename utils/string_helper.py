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
        import re

        match = re.search(r"([\d.]+)([万亿])?", text)
        if not match:
            return 0.0

        number = float(match.group(1))
        unit = match.group(2) if match.group(2) else ""

        # 处理单位转换
        if unit == "亿":
            return number * 100000000 if convert_unit else number
        elif unit == "万":
            return number * 10000 if convert_unit else number
        else:
            return number

    except (ValueError, IndexError, AttributeError):
        return 0.0
