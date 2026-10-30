import json
import hashlib
import random
import re
from pathlib import Path
from typing import Any

A11_FIELD_KEYS = ("modality_type", "field_of_view")
A11_ANSWER_KEYS = A11_FIELD_KEYS
A12_FIELD_KEYS = ("coverage_codes", "quality_grade")
A12_ANSWER_KEYS = A12_FIELD_KEYS
A13_FIELD_KEYS = ("sufficiency", "minimum_necessary_action")
A13_ANSWER_KEYS = A13_FIELD_KEYS
A21_FIELD_KEYS = ("dentition_stage",)
A21_ANSWER_KEYS = A21_FIELD_KEYS
A22_FIELD_KEYS = ("teeth",)
A22_ANSWER_KEYS = A22_FIELD_KEYS
A23_FIELD_KEYS = ("teeth",)
A23_ANSWER_KEYS = A23_FIELD_KEYS
A24_FIELD_KEYS = ("structures",)
A31_FIELD_KEYS = ("findings",)
A31_ANSWER_KEYS = A31_FIELD_KEYS
A24_ANSWER_KEYS = A24_FIELD_KEYS
A32_FIELD_KEYS = ("findings",)
A32_ANSWER_KEYS = A32_FIELD_KEYS
A33_FIELD_KEYS = ("findings",)
A33_ANSWER_KEYS = A33_FIELD_KEYS
A34_FIELD_KEYS = ("findings",)
A34_ANSWER_KEYS = A34_FIELD_KEYS
A41_FIELD_KEYS = ("grade_value",)
A41_ANSWER_KEYS = A41_FIELD_KEYS
A42_FIELD_KEYS = ("grade_value",)
A42_ANSWER_KEYS = A42_FIELD_KEYS
A43_FIELD_KEYS = ("surface_grades",)
A43_ANSWER_KEYS = A43_FIELD_KEYS

CLINICAL_FIELD_KEYS = {
    "A5.1": ("diagnoses", "reason"),
    "A5.2": ("diagnoses", "reason", "exclude_reason"),
    "A5.3": ("sufficiency", "reason"),
    "A6.1": ("total", "images"),
    "A6.2": ("diagnoses", "reason"),
    "A6.3": ("conditions",),
    "A7.1": ("plans",),
}

A43_SURFACE_LABELS = {
    "mesial": "近中面",
    "distal": "远中面",
    "occlusal": "咬合面",
    "buccal": "颊／唇面",
    "labial": "颊／唇面",
    "lingual": "舌／腭面",
    "palatal": "舌／腭面",
}
A43_SURFACE_ALIASES = {
    **A43_SURFACE_LABELS,
    **{label: label for label in A43_SURFACE_LABELS.values()},
    "颊/唇面": "颊／唇面",
    "舌/腭面": "舌／腭面",
}
A43_GRADE_OPTIONS = ("无龋", "浅龋", "中龋", "深龋")

A41_GRADE_LABELS = tuple(f"第{i}阶段" for i in range(1, 7))
A41_GRADE_ALIASES = {label: f"S{i}" for i, label in enumerate(A41_GRADE_LABELS, 1)}
A41_GRADE_ALIASES.update({f"S{i}": f"S{i}" for i in range(1, 7)})
A41_GRADE_ALIASES.update({
    label: f"S{i}"
    for i, label in enumerate(("第一阶段", "第二阶段", "第三阶段", "第四阶段", "第五阶段", "第六阶段"), 1)
})

MODALITY_OPTIONS = ("口内照", "黏膜照", "根尖片", "全景片", "头颅侧位片")
A11_VIEW_OPTIONS_BY_MODALITY = {
    "口内照": (
        "全口", "上颌", "下颌", "正面", "前牙区", "右侧后牙区", "左侧后牙区",
        "上颌前牙区", "下颌前牙区", "右上后牙区", "左上后牙区", "右下后牙区", "左下后牙区",
    ),
    "黏膜照": ("舌背", "舌腹", "舌缘", "左颊黏膜", "右颊黏膜", "上唇", "下唇", "上牙弓", "下牙弓"),
    "根尖片": (
        "上颌", "下颌", "前牙区", "右侧后牙区", "左侧后牙区",
        "上颌前牙区", "下颌前牙区", "右上后牙区", "左上后牙区", "右下后牙区", "左下后牙区",
    ),
    "全景片": ("全口",),
    "头颅侧位片": ("头颅侧位",),
}
VIEW_OPTIONS_BY_MODALITY = {
    "口内照": (
        "全口", "上颌", "下颌", "正面", "前牙区", "右侧后牙区", "左侧后牙区",
        "上颌前牙区", "下颌前牙区", "右上后牙区", "左上后牙区", "右下后牙区", "左下后牙区",
    ),
    "黏膜照": (
        "舌背", "舌腹", "舌缘", "舌根", "舌尖", "左颊黏膜", "右颊黏膜", "上唇", "下唇",
        "腭部", "口底", "上牙龈", "下牙龈", "上牙弓", "下牙弓", "其他口腔部位",
    ),
    "根尖片": (
        "上颌", "下颌", "前牙区", "右侧后牙区", "左侧后牙区",
        "上颌前牙区", "下颌前牙区", "右上后牙区", "左上后牙区", "右下后牙区", "左下后牙区",
    ),
    "全景片": ("全口",),
    "头颅侧位片": ("头颅侧位",),
}
NON_MUCOSA_VIEW_OPTIONS = (
    "全口", "头颅侧位", "上颌", "下颌", "正面", "前牙区", "右侧后牙区", "左侧后牙区",
    "上颌前牙区", "下颌前牙区", "右上后牙区", "左上后牙区", "右下后牙区", "左下后牙区",
)
A12_NON_MUCOSA_COVERAGE_OPTIONS = (
    "全口", "头颅侧位", "上颌", "下颌", "正面", "前牙区", "右侧后牙区", "左侧后牙区",
    "上颌前牙区", "下颌前牙区", "右上后牙区", "左上后牙区", "右下后牙区", "左下后牙区",
)
A12_MUCOSA_COVERAGE_OPTIONS = (
    "舌背", "舌腹", "舌缘", "左颊黏膜", "右颊黏膜", "上唇", "下唇", "上牙弓", "下牙弓",
)
A12_COVERAGE_OPTIONS = tuple(
    dict.fromkeys((*A12_NON_MUCOSA_COVERAGE_OPTIONS, *A12_MUCOSA_COVERAGE_OPTIONS, "部位无法判断"))
)
A12_QUALITY_LABEL_TO_CODE = {
    "未见明显问题": "adequate",
    "覆盖或部位辨识问题": "coverage_or_site",
    "成像质量问题": "image_quality",
}
A12_QUALITY_CODE_TO_LABEL = {value: key for key, value in A12_QUALITY_LABEL_TO_CODE.items()}

SUFFICIENCY_OPTIONS = ("充分", "不足")
ACTION_OPTIONS = (
    "无需补充检查",
    "重拍同一区域",
    "补充缺失视角",
    "补充目标牙根尖片",
    "补充咬翼片",
    "按标准重拍全景片",
    "补充限视野CBCT",
    "先行针对性临床检查",
    "补充牙髓活力检查",
    "补充牙周探诊",
    "补充标准化口内照片",
    "补充多视角黏膜照片",
    "补充活检病理",
)
OLD_ACTION_CODE_TO_LABEL = {
    "NO_ADDITIONAL_ACTION": "无需补充检查",
    "RETAKE_SAME_REGION": "重拍同一区域",
    "ADD_MISSING_VIEW": "补充缺失视角",
    "ADD_TARGETED_PERIAPICAL": "补充目标牙根尖片",
    "ADD_BITEWING": "补充咬翼片",
    "ADD_LIMITED_FOV_CBCT": "补充限视野CBCT",
    "CLINICAL_EXAM_FIRST": "先行针对性临床检查",
    "PULP_VITALITY_TEST": "补充牙髓活力检查",
    "ADD_PERIODONTAL_PROBING": "补充牙周探诊",
    "PERIODONTAL_PROBING": "补充牙周探诊",
    "ADD_STANDARDIZED_ORAL_PHOTOS": "补充标准化口内照片",
    "ADD_MULTI_VIEW_MUCOSA_PHOTOS": "补充多视角黏膜照片",
    "BIOPSY_PATHOLOGY": "补充活检病理",
    "REPEAT_STANDARD_PANORAMIC": "按标准重拍全景片",
    "OTHER_REVIEW": "其他 / 待审核",
}
DEPARTMENT_LABELS = {
    "ENDODONTICS": "牙体牙髓科",
    "ORAL_SURGERY": "口腔颌面外科",
    "PERIODONTOLOGY": "牙周科",
    "ORAL_MEDICINE": "口腔黏膜科",
    "PROSTHODONTICS": "口腔修复科",
    "PEDIATRIC_DENTISTRY": "儿童口腔科",
    "IMPLANTOLOGY": "口腔种植科",
    "ORTHODONTICS": "口腔正畸科",
}
GOAL_LABELS = {
    "ENDO_CARIES_ASSESSMENT": "龋损或继发龋评估",
    "ENDO_PERIAPICAL_ASSESSMENT": "根尖周异常评估",
    "ENDO_ROOT_CANAL_TREATMENT": "根管治疗及根管填充情况评估",
    "IMPLANT_PREOP_BONE": "种植术前骨量初步评估",
    "MUCOSA_MORPHOLOGY": "黏膜病变可见形态评估",
    "ORTHO_RECORD_COMPLETENESS": "正畸治疗前资料完整性判断",
    "PED_TOOTH_GERM_ERUPTION": "儿童牙胚/萌出评估",
    "PERIO_BONE_LOSS": "牙周骨丧失评估",
    "PERIO_STAGING_SUFFICIENCY": "牙周分期所需资料充分性判断",
    "PROS_PLAN_SUFFICIENCY": "修复方案制定所需资料充分性判断",
    "SURGERY_ANATOMIC_RELATIONSHIP": "外科解剖关系评估",
    "SURGERY_IMPACTED_POSITION": "阻生牙位置评估",
}
DENTITION_STAGE_OPTIONS = ("乳牙列", "混合牙列", "恒牙列")
UNEVALUABLE_REASON_OPTIONS = ("牙列覆盖不足", "年龄信息不足", "图像质量不足")
TOOTH_DEVELOPMENT_STATUS_OPTIONS = ("已萌出", "萌出中", "未萌出", "阻生", "缺失")
TOOTH_DEVELOPMENT_STATUS_ALIASES = {
    "缺牙": "缺失",
}
VALID_FDI_CODES = {
    *range(11, 19),
    *range(21, 29),
    *range(31, 39),
    *range(41, 49),
    *range(51, 56),
    *range(61, 66),
    *range(71, 76),
    *range(81, 86),
}
FDI_LEFT_TO_RIGHT_ORDER = (
    18, 17, 16, 15, 14, 13, 12, 11,
    21, 22, 23, 24, 25, 26, 27, 28,
    48, 47, 46, 45, 44, 43, 42, 41,
    31, 32, 33, 34, 35, 36, 37, 38,
    55, 54, 53, 52, 51,
    61, 62, 63, 64, 65,
    85, 84, 83, 82, 81,
    71, 72, 73, 74, 75,
)
FDI_LEFT_TO_RIGHT_RANK = {fdi: rank for rank, fdi in enumerate(FDI_LEFT_TO_RIGHT_ORDER)}
A31_FINDING_CODES = (
    "龋样缺损", "非龋性牙体缺损", "牙体折裂", "根尖周透射影", "根尖周阻射影",
    "牙周骨吸收", "牙根吸收", "牙根形态异常", "骨质异常",
)
A31_REGION_CODES = (
    "全口", "上颌", "下颌", "正面", "前牙区", "右侧后牙区", "左侧后牙区",
    "上颌前牙区", "下颌前牙区", "右上后牙区", "左上后牙区", "右下后牙区", "左下后牙区",
)
A32_FINDING_CODES = (
    "白色改变", "红色改变", "红白混合改变", "色素性改变", "溃疡", "糜烂",
    "水疱 / 大疱", "斑块样隆起", "丘疹 / 结节", "肿物", "萎缩", "其他/待审核",
)
A32_PROMPT_FINDING_CODES = A32_FINDING_CODES[:-1]
A32_FINDING_CODE_ALIASES = {
    "水疱/大疱": "水疱 / 大疱",
    "丘疹/结节": "丘疹 / 结节",
}
A32_REGION_CODES = (
    "舌背", "舌腹", "舌缘", "左颊黏膜", "右颊黏膜", "上唇", "下唇", "腭部", "上牙弓", "下牙弓",
)
A32_MODE_ALIASES = {
    "site_only": "region", "region": "region", "区域定位": "region",
    "box": "bbox", "bbox": "bbox", "画框定位": "bbox",
}
A33_FINDING_CODES = (
    "阻生", "异位萌出", "萌出延迟", "多生牙", "先天缺牙", "错位牙", "牙齿旋转",
    "拥挤", "牙列间隙", "深覆合", "深覆盖", "反合", "交叉合", "开合", "其他/待审核",
)
A33_PROMPT_FINDING_CODES = A33_FINDING_CODES[:-1]
A33_REGION_CODES = (
    "全口", "头颅侧位", "上颌", "下颌", "正面", "前牙区", "右侧后牙区", "左侧后牙区",
    "上颌前牙区", "下颌前牙区", "右上后牙区", "左上后牙区", "右下后牙区", "左下后牙区",
)
A33_FINDING_CODE_ALIASES = {}
A33_MODE_ALIASES = {
    "site_only": "region", "region": "region", "区域定位": "region",
    "tooth": "tooth", "fdi": "tooth", "牙位定位": "tooth",
    "box": "bbox", "bbox": "bbox", "画框定位": "bbox",
}
A34_FINDING_CODES = (
    "充填体", "嵌体 / 高嵌体", "根管充填", "桩核", "牙冠", "联冠", "固定桥",
    "种植体", "种植上部修复体", "正畸装置", "残根", "其他/待审核",
)
A34_PROMPT_FINDING_CODES = A34_FINDING_CODES[:-1]
A34_REGION_CODES = A33_REGION_CODES
A34_FINDING_CODE_ALIASES = {
    "嵌体/高嵌体": "嵌体 / 高嵌体",
}
A34_MODE_ALIASES = {
    "site_only": "region", "region": "region", "区域定位": "region",
    "tooth": "tooth", "fdi": "tooth", "牙位定位": "tooth",
    "box": "bbox", "bbox": "bbox", "画框定位": "bbox",
}
A31_MODE_ALIASES = {
    "local": "tooth", "fdi": "tooth", "tooth": "tooth", "site_only": "tooth", "牙位定位": "tooth",
    "box": "bbox", "bbox": "bbox", "画框定位": "bbox",
    "region": "region", "区域定位": "region",
}
CEPHALOMETRIC_STRUCTURE_LABELS = {
    "A": "A-point",
    "ANS": "Anterior Nasal Spine",
    "B": "B-point",
    "Me": "Menton",
    "N": "Nasion",
    "Or": "Orbitale",
    "Pog": "Pogonion",
    "PNS": "Posterior Nasal Spine",
    "Pn": "Pronasale",
    "R": "Ramus",
    "S": "Sella",
    "Ar": "Articulare",
    "Co": "Condylion",
    "Gn": "Gnathion",
    "Go": "Gonion",
    "Po": "Porion",
    "LPM": "Lower 2nd PM Cusp Tip",
    "LIT": "Lower Incisor Tip",
    "LMT": "Lower Molar Cusp Tip",
    "UPM": "Upper 2nd PM Cusp Tip",
    "UIA": "Upper Incisor Apex",
    "UIT": "Upper Incisor Tip",
    "UMT": "Upper Molar Cusp Tip",
    "LIA": "Lower Incisor Apex",
    "Li": "Labrale inferius",
    "Ls": "Labrale superius",
    "N`": "Soft Tissue Nasion",
    "Pog`": "Soft Tissue Pogonion",
    "Sn": "Subnasale",
}
CEPHALOMETRIC_STRUCTURE_ALIASES = {
    **{label: code for code, label in CEPHALOMETRIC_STRUCTURE_LABELS.items()},
    "A点": "A",
    "A point": "A",
    "鼻根点": "N",
    "蝶鞍点": "S",
    "眶点": "Or",
    "耳点": "Po",
    "前鼻棘": "ANS",
    "后鼻棘": "PNS",
    "颏下点": "Me",
    "颏前点": "Pog",
    "软组织鼻根点": "N`",
    "软组织颏前点": "Pog`",
    "鼻下点": "Sn",
    "鼻尖点": "Pn",
}
PERIAPICAL_STRUCTURE_CODE_TO_LABEL = {
    "MESIAL_CEJ": "近中釉牙骨质界",
    "DISTAL_CEJ": "远中釉牙骨质界",
    "ROOT_APEX": "根尖",
    "MESIAL_ALVEOLAR_CREST": "近中牙槽嵴顶",
    "DISTAL_ALVEOLAR_CREST": "远中牙槽嵴顶",
    "FURCATION": "根分叉",
}
PERIAPICAL_STRUCTURE_LABEL_TO_CODE = {
    label: code for code, label in PERIAPICAL_STRUCTURE_CODE_TO_LABEL.items()
}


def fields_to_dict(fields: list[dict[str, Any]], task_code: str | None = None) -> dict[str, Any]:
    values = {}
    for item in fields:
        key = str(item["key"])
        value = item["value"]
        if key == "minimum_necessary_action" and isinstance(value, dict):
            value = normalize_action_value(value)
        if key == "coverage_codes":
            value = normalize_coverage_codes(value)
        elif key == "quality_grade":
            value = normalize_quality_grade(value)
        elif key == "teeth":
            value = normalize_a22_teeth(value)
        elif key == "structures":
            value = normalize_a24_structures(value)
        elif key == "findings":
            if task_code == "A3.2":
                value = normalize_a32_findings(value)
            elif task_code == "A3.3":
                value = normalize_a33_findings(value)
            elif task_code == "A3.4":
                value = normalize_a34_findings(value)
            else:
                value = normalize_a31_findings(value)
        elif key == "surface_grades":
            value = normalize_a43_surface_grades(value)
        elif key == "target_teeth":
            key = "teeth"
            value = normalize_a23_teeth(value)
        elif key == "unevaluable_reasons":
            value = normalize_unevaluable_reasons(value)
        elif not isinstance(value, list):
            value = str(value).strip()
        values[key] = value
    return values


def option_letter(index: int) -> str:
    return chr(ord("A") + index)


def format_options(options: tuple[str, ...]) -> str:
    return " ".join(f"{option_letter(i)}. {value}" for i, value in enumerate(options))


def option_to_value(letter: str, options: tuple[str, ...]) -> str:
    normalized = str(letter).strip().upper()
    if len(normalized) != 1 or not normalized.isalpha():
        raise ValueError(f"invalid option letter: {letter}")

    index = ord(normalized) - ord("A")
    if index < 0 or index >= len(options):
        raise ValueError(f"option {letter} out of range for options: {options}")
    return options[index]


def build_a11_prompt(case: dict[str, Any]) -> str:
    return (
        "请观察提供的口腔影像，识别其模态类型和主要视野。\n\n"
        "模态类型只能选择一项：口内照、黏膜照、根尖片、全景片、头颅侧位片。\n\n"
        "非黏膜照的视野只能选择一项：全口、头颅侧位、上颌、下颌、正面、前牙区、右侧后牙区、左侧后牙区、上颌前牙区、下颌前牙区、右上后牙区、左上后牙区、右下后牙区、左下后牙区。\n\n"
        "黏膜照的视野只能选择一项：舌背、舌腹、舌缘、左颊黏膜、右颊黏膜、上唇、下唇、上牙弓、下牙弓。\n\n"
        "判定规则：\n"
        "1. 选择当前画面实际显示的主要解剖范围或视角，不推断画面之外的部位。\n"
        "2. 头颅侧位片的视野为头颅侧位，全景片的视野为全口。根尖片不能选全口、头颅侧位或正面；口内照不能选头颅侧位；黏膜照使用黏膜部位清单。\n"
        "3. 只回答模态与视野，不评价质量、疾病或临床用途。\n\n"
        "输出字段仅有modality_type和field_of_view，分别表示模态类型和主要视野。\n\n"
        "涉及左侧或右侧时，均以患者自身的左右侧为准。\n\n"
        "请仅输出以下格式的合法JSON对象，字段值从上述选项中选择，不添加其他字段、解释或代码围栏：\n"
        "{\n"
        '  "modality_type": "<模态类型>",\n'
        '  "field_of_view": "<主要视野>"\n'
        "}"
    )


def build_a12_prompt(case: dict[str, Any]) -> str:
    return (
        "请观察提供的口腔影像，给出实际覆盖范围和质量等级。\n\n"
        "覆盖范围只能选择一项，请选择最精确的一项。\n"
        "非粘膜照可选：全口、头颅侧位、上颌、下颌、正面、前牙区、右侧后牙区、左侧后牙区、上颌前牙区、下颌前牙区、右上后牙区、左上后牙区、右下后牙区、左下后牙区、部位无法判断。\n"
        "黏膜照可选：舌背、舌腹、舌缘、左颊黏膜、右颊黏膜、上唇、下唇、上牙弓、下牙弓、部位无法判断。\n"
        "只记录画面完整支持的范围，不推断未显示区域，不用多个同义范围重复表达同一视野。无法确认实际解剖部位时选择“部位无法判断”，不猜测细分部位。涉及左侧或右侧时，均以患者自身的左右侧为准。\n\n"
        "质量等级只能选择一项：\n"
        "- 未见明显问题：覆盖部位可辨，主要结构清楚，未见明显的关键结构裁切或成像缺陷。\n"
        "- 覆盖或部位辨识问题：画面较清楚，但关键结构被截断，或缺少辨认解剖部位所需的定位参照。\n"
        "- 成像质量问题：失焦、运动模糊、曝光异常、反光、遮挡或伪影等明显影响主要结构的观察。\n\n"
        "判定时注意：\n"
        "1. 局部视野不等于覆盖不足；未明显影响主要结构观察的轻微瑕疵，不单独判为有问题。\n"
        "2. 疾病或治疗表现本身不属于质量问题，不能将龋损、骨吸收或修复体直接视为成像缺陷。\n"
        "3. 三个选项表示问题性质，不表示严重程度。只根据当前画面判断，不假设临床用途。\n\n"
        "coverage_codes表示实际覆盖范围，为仅含一个元素的中文数组；quality_grade表示质量等级，使用上述三个中文选项之一。\n\n"
        "请仅按以下结构输出合法JSON，不增加其他字段、具体问题、判定理由或代码围栏：\n"
        "{\n"
        '  "coverage_codes": ["<实际覆盖范围>"],\n'
        '  "quality_grade": "<质量等级>"\n'
        "}"
    )


def build_a13_prompt(case: dict[str, Any]) -> str:
    purpose = next(
        item["value"] for item in case["input"].get("fields", []) if item.get("key") == "specified_purpose"
    )
    purpose_text = format_clinical_purpose(purpose)
    return (
        "请根据提供的影像和下列临床用途，判断现有信息是否充分，并选择一项最低必要行动。\n\n"
        f"临床用途：{purpose_text}\n\n"
        "充分性只能选择“充分”或“不足”。围绕指定的临床目标，综合影像模态、覆盖范围、可辨认程度和必要临床信息判断。影像清晰或存在局部质量问题，均不能单独决定充分性。\n\n"
        "最低必要行动只能选择一项：无需补充检查、重拍同一区域、补充缺失视角、补充目标牙根尖片、补充咬翼片、按标准重拍全景片、补充限视野CBCT、先行针对性临床检查、补充牙髓活力检查、补充牙周探诊、补充标准化口内照片、补充多视角黏膜照片、补充活检病理。\n\n"
        "判定与填写规则：\n"
        "1. 充分时选择“无需补充检查”；不足时选择一项针对关键证据缺口的最低必要行动。\n"
        "2. 仅依据影像和给定临床用途作答，不推测未提供的患者信息。\n"
        "3. 仅选择“补充缺失视角”时，才需从以下选项中选择一个具体视角／部位。普通视角允许：全口、头颅侧位、上颌、下颌、正面、前牙区、右侧后牙区、左侧后牙区、上颌前牙区、下颌前牙区、右上后牙区、左上后牙区、右下后牙区、左下后牙区。黏膜视角允许：舌背、舌腹、舌缘、舌根、舌尖、左颊黏膜、右颊黏膜、上唇、下唇、腭部、口底、上牙龈、下牙龈、上牙弓、下牙弓、其他口腔部位。\n"
        "4. 不输出行动理由、分级、诊断或治疗方案。\n\n"
        "sufficiency表示输入充分性；minimum_necessary_action用action_code记录所选行动。\n\n"
        "涉及左侧或右侧时，均以患者自身的左右侧为准。\n\n"
        "请仅按以下结构输出合法JSON；requested_view仅在action_code为“补充缺失视角”时保留并填写，其他行动删除此字段。不增加额外字段、正文说明或代码围栏：\n"
        "{\n"
        '  "sufficiency": "<充分或不足>",\n'
        '  "minimum_necessary_action": {\n'
        '    "action_code": "<一项最低必要行动>",\n'
        '    "requested_view": "<需补充的具体视角或部位>"\n'
        "  }\n"
        "}\n"
    )


# def build_a21_prompt(case: dict[str, Any]) -> str:
#     return (
#         "请观察提供的口腔影像，判断牙列阶段。\n\n"
#         "牙列阶段只能选择一项：乳牙列、混合牙列、恒牙列、不可评价。\n"
#         "不可评价原因可选：牙列覆盖不足、年龄信息不足、图像质量不足。\n\n"
#         "判定规则：\n"
#         "1. 根据可见的乳牙、恒牙及替牙特征判断，不推断未显示区域。\n"
#         "2. 无法可靠判断时选择“不可评价”，unevaluable_reasons至少填写一项原因，可多选但不重复；能够判断时该数组为空。\n"
#         "3. 仅在缺少年龄信息确实影响判断时，选择“年龄信息不足”。\n\n"
#         "请仅按以下结构输出合法JSON，不增加其他字段、说明或代码围栏：\n"
#         "{\n"
#         '  "dentition_stage": "<牙列阶段>",\n'
#         '  "unevaluable_reasons": []\n'
#         "}"
#     )
def build_a21_prompt(case: dict[str, Any]) -> str:
    return (
        "请观察提供的口腔影像，判断牙列阶段。\n\n"
        "牙列阶段只能选择一项：乳牙列、混合牙列、恒牙列。\n\n"
        "不可评价原因可选：牙列覆盖不足、年龄信息不足、图像质量不足。\n\n"
        "判定规则：\n"
        "1. 根据可见的乳牙、恒牙及替牙特征判断，不推断未显示区域。\n"
        "2. 仅在缺少年龄信息确实影响判断时，选择“年龄信息不足”。\n\n"
        "请仅按以下结构输出合法JSON，不增加其他字段、说明或代码围栏：\n"
        "{\n"
        '  "dentition_stage": "<牙列阶段>"\n'
        "}"
    )

def build_a22_prompt(case: dict[str, Any]) -> str:
    mode = get_field_value(case, "localization_mode")
    if mode == "inventory":
        return (
            "请观察提供的口腔影像，列出能够可靠识别的牙齿及其FDI编号。\n\n"
            "判定与输出规则：\n"
            "1. 识别画面中可确认的牙齿，FDI采用下列恒牙或乳牙编号，同一FDI只出现一次，按编号升序排列。\n"
            "2. 不补齐未显示或无法确认身份的牙位，不把仅有缺牙间隙的位置当作可见牙齿，不因为未萌出而自动忽略可识别牙齿。\n"
            "3. teeth直接填写FDI整数数组。\n\n"
            "牙位统一使用FDI整数，不加引号。恒牙仅限11–18、21–28、31–38、41–48；乳牙仅限51–55、61–65、71–75、81–85。\n\n"
            "请仅按以下示意结构输出合法JSON，示意牙位和坐标须替换为实际结果，不增加额外字段、说明或代码围栏：\n"
            "{\n"
            '  "teeth": [11, 12]\n'
            "}"
        )
    if mode == "detection":
        target_fdis = extract_a22_reference_fdis(case)
        target_fdis_text = json.dumps(target_fdis, ensure_ascii=False)
        return (
            "请在提供的口腔影像中定位下列指定FDI牙位，并分别给出完整牙体范围框。\n\n"
            f"待定位牙位：{target_fdis_text}\n\n"
            "判定与输出规则：\n"
            "1. 每个给定牙位记录一项，同一FDI只出现一次，按编号升序排列；不添加指定列表之外的牙位。\n"
            "2. 每项包含题目给定的fdi和对应bbox。框尽量贴合该牙实际可见的完整牙体，包含可见牙冠和牙根，覆盖所有可见根，不把邻牙、缺牙间隙或修复体单独作为一颗牙。\n"
            "3. bbox为当前画面上的归一化四数字数组。不能根据牙列平均位置生成框，也不以关键点代替框。\n\n"
            "牙位统一使用FDI整数，不加引号。恒牙仅限11–18、21–28、31–38、41–48；乳牙仅限51–55、61–65、71–75、81–85。\n\n"
            "坐标按实际影像填写：左上角为原点，向右、向下递增，按画面宽高归一化到0–1。框为[左边界,上边界,右边界,下边界]，左边界小于右边界，上边界小于下边界；四个值均为数字，四舍五入保留小数点后三位。\n\n"
            "请仅按以下结构模板输出合法JSON，不增加额外字段、说明或代码围栏：\n"
            "{\n"
            '  "teeth": [\n'
            "    {\n"
            '      "fdi": <题目给定的FDI整数>,\n'
            '      "bbox": [<左边界坐标>, <上边界坐标>, <右边界坐标>, <下边界坐标>]\n'
            "    }\n"
            "  ]\n"
            "}"
        )
    raise ValueError(f"unsupported A2.2 localization_mode: {mode}")


def build_a23_prompt(case: dict[str, Any]) -> str:
    target_fdis = extract_a23_target_fdis(case)
    target_fdis_text = json.dumps(target_fdis, ensure_ascii=False) if target_fdis else "{{题目给定的FDI整数数组}}"
    return (
        "请观察提供的口腔影像，判断待评价牙位的发育、萌出、缺失或阻生状态。\n\n"
        f"待评价牙位：{target_fdis_text}\n\n"
        "每颗目标牙的状态只能选择一项：已萌出、萌出中、未萌出、阻生、缺失。\n\n"
        "判定与输出规则：\n"
        "1. 仅记录待评价牙位中与发育、缺失或阻生情况有关的牙位，每项包含fdi和status；同一牙位只记录一次，按题目给定顺序输出，不添加其他牙位。\n"
        "2. 正常发育过程中未萌出不自动等于阻生；“阻生”需要有当前影像支持的异常位置、方向或萌出受阻表现，不能只因牙尚未萌出就判断阻生。\n"
        "3. “缺失”表示可可靠判读的牙位未见对应牙齿，未萌出牙仍存在时不标为缺失，不将区域未覆盖或牙位无法辨认判为缺失。\n"
        "4. 待评价牙位均可可靠判读，且均未见需记录的发育、缺失或阻生情况时，输出{\"teeth\": []}；不为正常牙位补齐记录。\n\n"
        "牙位统一使用FDI整数，不加引号。恒牙仅限11–18、21–28、31–38、41–48；乳牙仅限51–55、61–65、71–75、81–85。\n\n"
        "请仅按以下结构模板输出合法JSON，将数值占位符替换为实际数字，不加引号；不增加额外字段、说明或代码围栏：\n"
        "{\n"
        '  "teeth": [\n'
        '    {"fdi": <FDI整数>, "status": "<牙齿状态>"}\n'
        "  ]\n"
        "}"
    )


def build_a24_prompt(case: dict[str, Any]) -> str:
    modality = str(case.get("input", {}).get("images", [{}])[0].get("modality", "")).strip()
    if modality == "cephalometric_radiograph":
        target_structures = select_a24_cephalometric_structures(case)
        target_text = "、".join(target_structures) if target_structures else "{{题目指定的头影关键点中文列表}}"
        return (
            "请在提供的头影影像中定位下列指定关键点，并给出各点的坐标。\n\n"
            f"待定位关键点：{target_text}" "\n\n"
            "头影结构：A · A-point；ANS · Anterior Nasal Spine；B · B-point；Me · Menton；N · Nasion；Or · Orbitale；Pog · Pogonion；PNS · Posterior Nasal Spine；Pn · Pronasale；R · Ramus；S · Sella；Ar · Articulare；Co · Condylion；Gn · Gnathion；Go · Gonion；Po · Porion；LPM · Lower 2nd PM Cusp Tip；LIT · Lower Incisor Tip；LMT · Lower Molar Cusp Tip；UPM · Upper 2nd PM Cusp Tip；UIA · Upper Incisor Apex；UIT · Upper Incisor Tip；UMT · Upper Molar Cusp Tip；LIA · Lower Incisor Apex；Li · Labrale inferius；Ls · Labrale superius；N` · Soft Tissue Nasion；Pog` · Soft Tissue Pogonion；Sn · Subnasale。\n\n"
            "判定与输出规则：\n"
            "1. 只定位题目指定的关键点，每个点记录一次，按给定列表的顺序排列。\n"
            "2. structure_code使用题目给定的点名，coordinate记录该点的坐标。\n"
            "3. 区分骨组织、软组织、牙尖、切缘和根尖等不同点位，不合并名称相近的关键点。\n\n"
            "坐标按实际影像填写：左上角为原点，向右、向下递增，按画面宽高归一化到0-1。点为[横坐标,纵坐标]，两个值均为数字。\n\n"
            "请仅按以下结构模板输出合法JSON，将数值占位符替换为实际数字，不加引号；不增加额外字段、说明或代码围栏：\n"
            "{\n"
            '  "structures": [\n'
            "    {\n"
            '      "structure_code": "<题目指定的头影关键点名称>",\n'
            '      "coordinate": [<横坐标>, <纵坐标>]\n'
            "    }\n"
            "  ]\n"
            "}"
        )
    if modality == "periapical_radiograph":
        image_fdis = extract_a24_periapical_image_fdis(case)
        target_fdis = select_a24_periapical_target_fdis(case)
        left_to_right_fdis = extract_a24_periapical_left_to_right_fdis(case)
        image_fdis_text = json.dumps(image_fdis, ensure_ascii=False) if image_fdis else "{{图中牙齿FDI整数数组}}"
        target_fdi_text = str(target_fdis[0]) if target_fdis else "{{需定位关键点的目标牙FDI整数}}"
        left_to_right_fdis_text = "、".join(str(fdi) for fdi in left_to_right_fdis) if left_to_right_fdis else "{{从左到右的FDI整数序列}}"
        return (
            "请根据提供的根尖片及图中牙位信息，定位下列目标牙的牙周关键点，并给出各点的坐标。\n\n"
            f"图中包含的牙位从左到右依次是：{image_fdis_text}\n"
            f"目标牙位：{target_fdi_text}\n\n"
            "关键点类型：近中釉牙骨质界、远中釉牙骨质界、根尖、近中牙槽嵴顶、远中牙槽嵴顶、根分叉。\n\n"
            "判定与输出规则：\n"
            "1. 只为目标牙位记录关键点；图中包含的其他牙位用于位置参照，不输出其点位。\n"
            "2. 每项包含structure_code和coordinate，分别记录点名及点坐标。同一牙位下同一类型最多记录一次。\n"
            "3. 记录目标牙实际存在且可辨认的上述关键点；根分叉仅对存在根分叉的目标牙记录。\n"
            "4. 近中、远中按牙齿与牙弓中线的关系判断。\n\n"
            "牙位统一使用FDI整数，不加引号。恒牙仅限11-18、21-28、31-38、41-48；乳牙仅限51-55、61-65、71-75、81-85。\n\n"
            "坐标按实际影像填写：左上角为原点，向右、向下递增，按画面宽高归一化到0-1。点为[横坐标,纵坐标]，两个值均为数字。\n\n"
            "请仅按以下结构模板输出合法JSON，将数值占位符替换为实际数字，不加引号；不增加额外字段、说明或代码围栏：\n"
            "{\n"
            '  "structures": [\n'
            "    {\n"
            '      "structure_code": "<牙周关键点名称>",\n'
            '      "coordinate": [<横坐标>, <纵坐标>]\n'
            "    }\n"
            "  ]\n"
            "}"
        )
    raise ValueError(f"unsupported A2.4 modality: {modality}")


def get_a31_scope(case: dict[str, Any]) -> dict[str, Any]:
    raw = get_field_value(case, "evaluation_scope")
    if not isinstance(raw, dict):
        raw = {}
    concepts = raw.get("concept_codes") or []
    concepts = [str(item).strip() for item in concepts if str(item).strip() and str(item) != "__UNSPECIFIED_FINDING__"]
    site = raw.get("site") or {}
    site_type = str(site.get("type", "whole_mouth")).strip()
    fdis = [normalize_fdi(item) for item in site.get("fdi", [])] if site_type == "tooth" else []
    regions = [str(item).strip() for item in site.get("region_codes", []) if str(item).strip()]
    return {"concepts": concepts, "site_type": site_type, "fdis": sorted(set(fdis)), "regions": regions}


def get_a31_mode(case: dict[str, Any]) -> str:
    value = get_field_value(case, "evaluation_scope")
    mode = value.get("localization_mode") if isinstance(value, dict) else None
    fallback = A31_MODE_ALIASES.get(str(mode or "local").strip(), str(mode or "local").strip())
    return infer_reference_localization_mode(case, A31_MODE_ALIASES, fallback)


def _a31_reference_finding_codes(case: dict[str, Any]) -> list[str]:
    """Return unique reference labels used to build the case-local choices."""
    for field in case.get("reference_answer", {}).get("fields", []):
        if field.get("key") != "findings" or not isinstance(field.get("value"), list):
            continue
        codes = {
            str(item.get("finding_code")).strip()
            for item in field["value"]
            if isinstance(item, dict) and str(item.get("finding_code", "")).strip() in A31_FINDING_CODES
        }
        return [code for code in A31_FINDING_CODES if code in codes]
    return []


def _a31_choice_options(case: dict[str, Any]) -> list[str]:
    """Build six deterministic choices containing every correct A3.1 label."""
    correct = _a31_reference_finding_codes(case)
    if len(correct) > 6:
        raise ValueError(f"A3.1 has more than six correct finding codes: {correct}")
    pool = A31_FINDING_CODES
    distractors = [code for code in pool if code not in correct]
    seed_text = "A3.1|finding-options|{}|{}".format(
        case.get("id", ""), case.get("case_code", "")
    )
    seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    rng.shuffle(distractors)
    options = [*correct, *distractors[: 6 - len(correct)]]
    rng.shuffle(options)
    return options


def build_a31_prompt(case: dict[str, Any]) -> str:
    scope = get_a31_scope(case)
    mode = get_a31_mode(case)
    category_text = json.dumps(scope["concepts"], ensure_ascii=False) if scope["concepts"] else "未指定"
    category_options = _a31_choice_options(case)
    category_options_text = "、".join(category_options)
    if scope["site_type"] == "tooth" and scope["fdis"]:
        scope_text = json.dumps(scope["fdis"], ensure_ascii=False)
    elif scope["site_type"] == "region" and scope["regions"]:
        scope_text = json.dumps(scope["regions"], ensure_ascii=False)
    else:
        scope_text = "全口"
    common = (
        "请观察提供的口腔影像，查找硬组织异常。\n\n"
        f"评价类别：{category_text}\n"
        f"评价范围：{scope_text}\n\n"
        f"硬组织异常类别：{category_options_text}\n"
        "指定评价类别时，仅检查指定类别；未指定时，检查并列出上述全部类别中实际存在的异常。\n\n"
    )
    if mode == "tooth":
        return common + (
            "判定规则：\n"
            "1. 未见需记录的异常时，输出{\"findings\": []}。\n"
            "2. 按牙位定位，每项包含finding_code和非空FDI整数数组fdi。指定牙位时仅评价这些牙位；全口时评价影像中所有可判读的牙位。\n"
            "3. 同种类型的异常合并为一条记录，fdi汇总所有相关牙位，去重并按FDI编号升序排列。同一牙位存在多种异常时，分别记录在对应类别中。\n\n"
            "牙位统一使用FDI整数，不加引号。恒牙仅限11–18、21–28、31–38、41–48；乳牙仅限51–55、61–65、71–75、81–85。\n\n"
            "请仅输出一个合法JSON对象，按以下结构填写，不加引号，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的硬组织异常类别>\",\n      \"fdi\": [<FDI整数>]\n    }\n  ]\n}"
        )
    if mode == "bbox":
        return common + (
            "判定规则：\n"
            "1. 未见需记录的异常时，输出{\"findings\": []}。\n"
            "2. 按框定位，每项只包含finding_code和bbox，每个框对应一个类别，只记录评价范围内的目标。\n"
            "3. 不同目标分别画框，即使类别相同也不合并；同一目标有多种所见时，按类别分别记录。\n"
            "4. 框尽量贴合异常的实际可见范围，不包含无关的邻近结构。\n\n"
            "坐标以实际影像为准：左上角为原点，向右、向下递增，按画面宽高归一化到0–1。bbox为[左边界,上边界,右边界,下边界]，左边界小于右边界，上边界小于下边界；四个值均为数字，四舍五入保留小数点后三位。\n\n"
            "请仅输出一个合法JSON对象，按以下结构填写，不加引号，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的硬组织异常类别>\",\n      \"bbox\": [<左边界坐标>, <上边界坐标>, <右边界坐标>, <下边界坐标>]\n    }\n  ]\n}"
        )
    raise ValueError(f"unsupported A3.1 localization_mode: {mode}")


def infer_reference_localization_mode(case: dict[str, Any], aliases: dict[str, str], fallback: str) -> str:
    findings: list[dict[str, Any]] = []
    for field in case.get("reference_answer", {}).get("fields", []):
        if field.get("key") == "findings" and isinstance(field.get("value"), list):
            findings = field["value"]
            break
    if any("bbox" in item or "normalized_bbox" in item for item in findings if isinstance(item, dict)):
        return aliases.get("bbox", "bbox")
    if any(
        "fdi" in item
        or (isinstance(item.get("site"), dict) and item["site"].get("type") == "tooth")
        for item in findings
        if isinstance(item, dict)
    ):
        return aliases.get("tooth", "tooth")
    if any(
        "region_code" in item
        or "region_codes" in item
        or (isinstance(item.get("site"), dict) and item["site"].get("type") == "region")
        for item in findings
        if isinstance(item, dict)
    ):
        return aliases.get("region", "region")
    return fallback


def get_a32_scope(case: dict[str, Any]) -> dict[str, Any]:
    raw = get_field_value(case, "evaluation_scope")
    if not isinstance(raw, dict):
        raw = {}
    other_text = str(raw.get("other_text") or "").strip()
    concepts = [
        str(item).strip()
        for item in raw.get("concept_codes", []) or []
        if str(item).strip() and str(item) != "__UNSPECIFIED_FINDING__"
    ]
    concepts = [concept for concept in concepts if concept != "其他/待审核"]
    if other_text and "其他/待审核" in (raw.get("concept_codes") or []):
        concepts.append(other_text)
    site = raw.get("site") or {}
    regions = [str(item).strip() for item in site.get("region_codes", []) if str(item).strip()]
    fallback = A32_MODE_ALIASES.get(str(raw.get("localization_mode") or "region").strip(), "region")
    mode = infer_reference_localization_mode(case, A32_MODE_ALIASES, fallback)
    return {"concepts": concepts, "other_text": other_text, "regions": regions, "mode": mode}


def _a32_reference_finding_codes(case: dict[str, Any]) -> list[str]:
    """Return unique reference labels used to build the six A3.2 choices."""
    for field in case.get("reference_answer", {}).get("fields", []):
        if field.get("key") != "findings" or not isinstance(field.get("value"), list):
            continue
        codes: list[str] = []
        for item in field["value"]:
            if not isinstance(item, dict):
                continue
            raw_code = str(item.get("finding_code", "")).strip()
            code = A32_FINDING_CODE_ALIASES.get(raw_code, raw_code)
            if code == "其他/待审核":
                code = str(item.get("other_text") or code).strip()
            if code and code not in codes:
                codes.append(code)
        return codes
    return []


def _a32_choice_options(case: dict[str, Any]) -> list[str]:
    """Build six deterministic choices containing every correct A3.2 label."""
    correct = _a32_reference_finding_codes(case)
    if len(correct) > 6:
        raise ValueError(f"A3.2 has more than six correct finding codes: {correct}")
    pool = list(A32_PROMPT_FINDING_CODES)
    distractors = [code for code in pool if code not in correct]
    seed_text = "A3.2|{}|{}".format(
        case.get("id", ""),
        case.get("case_code", ""),
    )
    seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    rng.shuffle(distractors)
    options = [*correct, *distractors[: 6 - len(correct)]]
    rng.shuffle(options)
    return options


def build_a32_prompt(case: dict[str, Any]) -> str:
    scope = get_a32_scope(case)
    category_text = json.dumps(scope["concepts"], ensure_ascii=False) if scope["concepts"] else "未指定"
    category_options_text = "、".join(_a32_choice_options(case))
    scope_text = json.dumps(scope["regions"], ensure_ascii=False) if scope["regions"] else "全口"
    common = (
        "请观察提供的口腔照片，查找软组织异常。\n\n"
        f"评价类别：{category_text}\n"
        f"评价范围：{scope_text}\n\n"
        f"软组织表现类别：{category_options_text}\n"
        "finding_code只能从上述软组织表现类别选项中选择，可多选。\n"
        "指定评价类别时，仅检查指定类别；未指定时，检查并列出上述全部类别中实际存在的所见。\n\n"
    )
    if scope["mode"] == "region":
        return common + (
            "判定规则：\n"
            "1. 未见需记录的所见时，输出{\"findings\": []}。\n"
            "2. 按区域定位，每项只包含finding_code和region_code，region_code为非空的中文区域名称数组；评价范围为全口，区域须来自下方区域词表，只记录影像中可判读的所见。\n"
            "3. 同一类别合并为一条记录，region_code汇总所有相关区域，去重并按题面评价范围的顺序排列。同一区域存在多种类别时，分别记录在对应类别中。\n"
            "4. 记录照片中可见的软组织表现，不将反光、唾液或器械遮挡当作病损，不据此确定病理诊断。\n\n"
            "区域词表：舌背、舌腹、舌缘、左颊黏膜、右颊黏膜、上唇、下唇、腭部、上牙弓、下牙弓。\n"
            "涉及左侧或右侧时，均以患者自身的左右侧为准。\n\n"
            "请仅输出一个合法JSON对象，按以下结构模板填写，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的软组织表现类别>\",\n      \"region_code\": [\"<评价范围中允许的中文区域名称>\"]\n    }\n  ]\n}"
        )
    if scope["mode"] == "bbox":
        return common + (
            "判定规则：\n"
            "1. 未见需记录的所见时，输出{\"findings\": []}。\n"
            "2. 按框定位，每项只包含finding_code和bbox，每个框对应一个类别，只记录评价范围内的目标。\n"
            "3. 不同目标分别画框，即使类别相同也不合并；同一目标有多种所见时，按类别分别记录。\n"
            "4. 框尽量贴合目标软组织表现的实际可见范围，不包含无关的周围组织。\n\n"
            "坐标以实际影像为准：左上角为原点，向右、向下递增，按画面宽高归一化到0–1。bbox为[左边界,上边界,右边界,下边界]，左边界小于右边界，上边界小于下边界；四个值均为数字，四舍五入保留小数点后三位。\n\n"
            "请仅输出一个合法JSON对象，按以下结构模板填写；将坐标占位符替换为实际数字，不加引号，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的软组织表现类别>\",\n      \"bbox\": [<左边界坐标>, <上边界坐标>, <右边界坐标>, <下边界坐标>]\n    }\n  ]\n}"
        )
    raise ValueError(f"unsupported A3.2 localization_mode: {scope['mode']}")


def get_a33_scope(case: dict[str, Any]) -> dict[str, Any]:
    raw = get_field_value(case, "evaluation_scope")
    if not isinstance(raw, dict):
        raw = {}
    raw_concepts = [str(item).strip() for item in raw.get("concept_codes", []) or [] if str(item).strip()]
    other_text = str(raw.get("other_text") or "").strip()
    concepts = [concept for concept in raw_concepts if concept not in {"__UNSPECIFIED_FINDING__", "其他/待审核"}]
    if other_text and "其他/待审核" in raw_concepts:
        concepts.append(other_text)
    site = raw.get("site") or {}
    site_type = str(site.get("type", "whole_mouth")).strip()
    fdis = [normalize_fdi(item) for item in site.get("fdi", [])] if site_type == "tooth" else []
    regions = [str(item).strip() for item in site.get("region_codes", []) if str(item).strip()]
    raw_mode = raw.get("localization_mode")
    if raw_mode:
        mode = A33_MODE_ALIASES.get(str(raw_mode).strip(), str(raw_mode).strip())
    elif site_type == "tooth":
        mode = "tooth"
    else:
        mode = "region"
    mode = infer_reference_localization_mode(case, A33_MODE_ALIASES, mode)
    return {"concepts": concepts, "other_text": other_text, "site_type": site_type, "fdis": sorted(set(fdis)), "regions": regions, "mode": mode}


def _a33_reference_finding_codes(case: dict[str, Any]) -> list[str]:
    """Return unique reference labels used to build the six A3.3 choices."""
    for field in case.get("reference_answer", {}).get("fields", []):
        if field.get("key") != "findings" or not isinstance(field.get("value"), list):
            continue
        codes: list[str] = []
        for item in field["value"]:
            if not isinstance(item, dict):
                continue
            code = str(item.get("finding_code", "")).strip()
            if code == "其他/待审核":
                code = str(item.get("other_text") or code).strip()
            if code and code not in codes:
                codes.append(code)
        return codes
    return []


def _a33_choice_options(case: dict[str, Any]) -> list[str]:
    """Build six deterministic choices containing every correct A3.3 label."""
    correct = _a33_reference_finding_codes(case)
    if len(correct) > 6:
        raise ValueError(f"A3.3 has more than six correct finding codes: {correct}")
    pool = list(A33_PROMPT_FINDING_CODES)
    distractors = [code for code in pool if code not in correct]
    seed_text = "A3.3|{}|{}".format(
        case.get("id", ""),
        case.get("case_code", ""),
    )
    seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    rng.shuffle(distractors)
    options = [*correct, *distractors[: 6 - len(correct)]]
    rng.shuffle(options)
    return options


def build_a33_prompt(case: dict[str, Any]) -> str:
    scope = get_a33_scope(case)
    category_text = json.dumps(scope["concepts"], ensure_ascii=False) if scope["concepts"] else "未指定"
    category_options_text = "、".join(_a33_choice_options(case))
    if scope["mode"] == "region":
        # 区域定位时要求模型先在全口范围内观察，再返回具体区域。
        scope_text = "全口"
    elif scope["site_type"] == "tooth":
        scope_text = json.dumps(scope["fdis"], ensure_ascii=False) if scope["fdis"] else "全口"
    elif scope["site_type"] == "region":
        scope_text = json.dumps(scope["regions"], ensure_ascii=False) if scope["regions"] else "全口"
    elif scope["mode"] == "region":
        scope_text = "全口"
    else:
        scope_parts = []
        if scope["fdis"]:
            scope_parts.append(json.dumps(scope["fdis"], ensure_ascii=False))
        if scope["regions"]:
            scope_parts.append(json.dumps(scope["regions"], ensure_ascii=False))
        scope_text = "、".join(scope_parts) if scope_parts else "全口"
    common = (
        "请观察提供的口腔影像，查找正畸或发育异常。\n\n"
        f"评价类别：{category_text}\n"
        f"评价范围：{scope_text}\n\n"
        f"正畸／发育异常类别：{category_options_text}\n"
        "finding_code只能从上述正畸／发育异常类别选项中选择，可多选。\n"
        "指定评价类别时，仅检查指定类别；未指定时，检查并列出上述全部类别中实际存在的异常。\n\n"
    )
    if scope["mode"] == "tooth":
        return common + (
            "判定规则：\n"
            "1. 未见需记录的异常时，输出{\"findings\": []}。\n"
            "2. 按牙位定位，每项包含finding_code和非空FDI整数数组fdi。指定牙位时仅评价这些牙位；全口时评价影像中所有可判读的牙位。\n"
            "3. 同种类型的异常合并为一条记录，fdi汇总所有相关牙位，去重并按FDI编号升序排列。同一牙位存在多种异常时，分别记录在对应类别中。\n\n"
            "牙位统一使用FDI整数，不加引号。恒牙仅限11–18、21–28、31–38、41–48；乳牙仅限51–55、61–65、71–75、81–85。\n\n"
            "请仅输出一个合法JSON对象，按以下结构模板填写；将数值占位符替换为实际数字，不加引号，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的正畸或发育异常类别>\",\n      \"fdi\": [<FDI整数>]\n    }\n  ]\n}"
        )
    if scope["mode"] == "region":
        return common + (
            "区域词表：全口、头颅侧位、上颌、下颌、正面、前牙区、右侧后牙区、左侧后牙区、上颌前牙区、下颌前牙区、右上后牙区、左上后牙区、右下后牙区、左下后牙区。\n\n"
            "判定规则：\n"
            "1. 未见需记录的异常时，输出{\"findings\": []}。\n"
            "2. 按区域定位，每项只包含finding_code和region_code，region_code为非空的中文区域名称数组；评价范围为全口，区域须来自下方区域词表，只记录影像中可判读的所见。\n"
            "3. 同一类别合并为一条记录，region_code汇总所有相关区域，去重并按题面评价范围的顺序排列。同一区域存在多种类别时，分别记录在对应类别中。\n"
            "4. 牙列或咬合关系按其涉及的区域记录；未萌出不直接等于阻生或萌出延迟，当前未见牙齿不直接等于先天缺牙，咬合关系未显示时不推断咬合异常。\n\n"
            "涉及左侧或右侧时，均以患者自身的左右侧为准。\n\n"
            "请仅输出一个合法JSON对象，按以下结构模板填写，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的正畸／发育异常类别>\",\n      \"region_code\": [\"<评价范围中允许的中文区域名称>\"]\n    }\n  ]\n}"
        )
    if scope["mode"] == "bbox":
        return common + (
            "判定规则：\n"
            "1. 未见需记录的异常时，输出{\"findings\": []}。\n"
            "2. 按框定位，每项只包含finding_code和bbox，每个框对应一个类别，只记录评价范围内的目标。\n"
            "3. 不同目标分别画框，即使类别相同也不合并；同一目标有多种所见时，按类别分别记录。\n"
            "4. 框覆盖支持该异常的相关牙齿或咬合结构；同一个牙列或咬合关系涉及多颗牙时，用一个框覆盖该关系所需的完整范围。\n\n"
            "坐标以实际影像为准：左上角为原点，向右、向下递增，按画面宽高归一化到0–1。bbox为[左边界,上边界,右边界,下边界]，左边界小于右边界，上边界小于下边界；四个值均为数字，四舍五入保留小数点后三位。\n\n"
            "请仅输出一个合法JSON对象，按以下结构模板填写；将坐标占位符替换为实际数字，不加引号，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的正畸／发育异常类别>\",\n      \"bbox\": [<左边界坐标>, <上边界坐标>, <右边界坐标>, <下边界坐标>]\n    }\n  ]\n}"
        )
    raise ValueError(f"unsupported A3.3 localization_mode: {scope['mode']}")


def get_a34_scope(case: dict[str, Any]) -> dict[str, Any]:
    raw = get_field_value(case, "evaluation_scope")
    if not isinstance(raw, dict):
        raw = {}
    raw_concepts = [str(item).strip() for item in raw.get("concept_codes", []) or [] if str(item).strip()]
    other_text = str(raw.get("other_text") or "").strip()
    concepts = [concept for concept in raw_concepts if concept not in {"__UNSPECIFIED_FINDING__", "其他/待审核"}]
    if other_text and "其他/待审核" in raw_concepts:
        concepts.append(other_text)
    site = raw.get("site") or {}
    site_type = str(site.get("type", "whole_mouth")).strip()
    fdis = [normalize_fdi(item) for item in site.get("fdi", [])] if site_type == "tooth" else []
    regions = [str(item).strip() for item in site.get("region_codes", []) if str(item).strip()]
    raw_mode = raw.get("localization_mode")
    if raw_mode:
        mode = A34_MODE_ALIASES.get(str(raw_mode).strip(), str(raw_mode).strip())
    elif site_type == "tooth":
        mode = "tooth"
    else:
        mode = "region"
    mode = infer_reference_localization_mode(case, A34_MODE_ALIASES, mode)
    return {"concepts": concepts, "site_type": site_type, "fdis": sorted(set(fdis)), "regions": regions, "mode": mode}


def _a34_reference_finding_codes(case: dict[str, Any]) -> list[str]:
    """Return unique reference labels used to build the six A3.4 choices."""
    for field in case.get("reference_answer", {}).get("fields", []):
        if field.get("key") != "findings" or not isinstance(field.get("value"), list):
            continue
        codes: list[str] = []
        for item in field["value"]:
            if not isinstance(item, dict):
                continue
            raw_code = str(item.get("finding_code", "")).strip()
            code = A34_FINDING_CODE_ALIASES.get(raw_code, raw_code)
            if code == "其他/待审核":
                code = str(item.get("other_text") or code).strip()
            if code and code not in codes:
                codes.append(code)
        return codes
    return []


def _a34_choice_options(case: dict[str, Any]) -> list[str]:
    """Build six deterministic choices containing every correct A3.4 label."""
    correct = _a34_reference_finding_codes(case)
    if len(correct) > 6:
        raise ValueError(f"A3.4 has more than six correct finding codes: {correct}")
    distractors = [code for code in A34_PROMPT_FINDING_CODES if code not in correct]
    seed_text = "A3.4|{}|{}".format(
        case.get("id", ""),
        case.get("case_code", ""),
    )
    seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    rng.shuffle(distractors)
    options = [*correct, *distractors[: 6 - len(correct)]]
    rng.shuffle(options)
    return options


def build_a34_prompt(case: dict[str, Any]) -> str:
    scope = get_a34_scope(case)
    category_text = json.dumps(scope["concepts"], ensure_ascii=False) if scope["concepts"] else "未指定"
    category_options_text = "、".join(_a34_choice_options(case))
    if scope["mode"] == "region":
        # 区域定位时要求模型先在全口范围内观察，再返回具体区域。
        scope_text = "全口"
    elif scope["site_type"] == "tooth":
        scope_text = json.dumps(scope["fdis"], ensure_ascii=False) if scope["fdis"] else "全口"
    elif scope["site_type"] == "region":
        scope_text = json.dumps(scope["regions"], ensure_ascii=False) if scope["regions"] else "全口"
    elif scope["mode"] == "region":
        scope_text = "全口"
    else:
        parts = []
        if scope["fdis"]:
            parts.append(json.dumps(scope["fdis"], ensure_ascii=False))
        if scope["regions"]:
            parts.append(json.dumps(scope["regions"], ensure_ascii=False))
        scope_text = "、".join(parts) if parts else "全口"
    common = (
        "请观察提供的口腔影像，识别治疗、修复及相关状态。\n\n"
        f"评价类别：{category_text}\n"
        f"评价范围：{scope_text}\n\n"
        f"治疗状态类别：{category_options_text}\n"
        "finding_code只能从上述治疗状态类别选项中选择，可多选。\n"
        "指定评价类别时，仅检查指定类别；未指定时，检查并列出上述全部类别中实际存在的所见。\n\n"
    )
    if scope["mode"] == "tooth":
        return common + (
            "判定规则：\n"
            "1. 未见需记录的所见时，输出{\"findings\": []}。\n"
            "2. 按牙位定位，每项包含finding_code和非空FDI整数数组fdi。指定牙位时仅评价这些牙位；全口时评价影像中所有可判读的牙位。\n"
            "3. 除固定桥每座单独记录外，同种类型的所见合并为一条记录，fdi汇总所有相关牙位，去重并按FDI编号升序排列。同一牙位存在多种所见时，分别记录在对应类别中。\n"
            "4. 每座固定桥记录一项，finding_code为“固定桥”，fdi合并评价范围内的基牙位与桥体替代的缺牙位，按患者右侧到左侧排列；缺牙位仍填写对应FDI。单冠或没有桥体替代缺牙位的联冠，不标为固定桥。\n\n"
            "牙位统一使用FDI整数，不加引号。恒牙仅限11–18、21–28、31–38、41–48；乳牙仅限51–55、61–65、71–75、81–85。\n\n"
            "请仅输出一个合法JSON对象，按以下结构模板填写；将数值占位符替换为实际数字，不加引号，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的治疗状态类别>\",\n      \"fdi\": [<FDI整数>]\n    }\n  ]\n}"
        )
    if scope["mode"] == "region":
        return common + (
            "区域词表：全口、头颅侧位、上颌、下颌、正面、前牙区、右侧后牙区、左侧后牙区、上颌前牙区、下颌前牙区、右上后牙区、左上后牙区、右下后牙区、左下后牙区。\n\n"
            "判定规则：\n"
            "1. 未见需记录的所见时，输出{\"findings\": []}。\n"
            "2. 按区域定位，每项只包含finding_code和region_code，region_code为非空的中文区域名称数组；评价范围为全口，区域须来自下方区域词表，只记录影像中可判读的所见。\n"
            "3. 同一类别合并为一条记录，region_code汇总所有相关区域，去重并按题面评价范围的顺序排列。同一区域存在多种类别时，分别记录在对应类别中。\n"
            "4. 固定桥按包含基牙及桥体的完整修复体确定所在区域；单冠或没有桥体替代缺牙位的联冠，不标为固定桥。\n\n"
            "涉及左侧或右侧时，均以患者自身的左右侧为准。\n\n"
            "请仅输出一个合法JSON对象，按以下结构模板填写，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的治疗状态类别>\",\n      \"region_code\": [\"<评价范围中允许的中文区域名称>\"]\n    }\n  ]\n}"
        )
    if scope["mode"] == "bbox":
        return common + (
            "判定规则：\n"
            "1. 未见需记录的所见时，输出{\"findings\": []}。\n"
            "2. 按框定位，每项只包含finding_code和bbox，每个框对应一个类别，只记录评价范围内的目标。\n"
            "3. 不同目标分别画框，即使类别相同也不合并；同一目标有多种所见时，按类别分别记录。\n"
            "4. 框尽量贴合目标治疗或修复所见的实际可见范围；每座固定桥或每组联冠各用一个框，包含该修复体的全部可见组成部分。\n\n"
            "坐标以实际影像为准：左上角为原点，向右、向下递增，按画面宽高归一化到0–1。bbox为[左边界,上边界,右边界,下边界]，左边界小于右边界，上边界小于下边界；四个值均为数字，四舍五入保留小数点后三位。\n\n"
            "请仅输出一个合法JSON对象，按以下结构模板填写；将坐标占位符替换为实际数字，不加引号，不增加额外字段、说明或代码围栏：\n"
            "{\n  \"findings\": [\n    {\n      \"finding_code\": \"<实际发现的治疗状态类别>\",\n      \"bbox\": [<左边界坐标>, <上边界坐标>, <右边界坐标>, <下边界坐标>]\n    }\n  ]\n}"
        )
    raise ValueError(f"unsupported A3.4 localization_mode: {scope['mode']}")


def build_a41_prompt(case: dict[str, Any]) -> str:
    return (
        "请观察提供的头颅侧位片，根据第2至第4颈椎的可见形态，按下列标准判断颈椎成熟阶段。\n\n"
        "采用以下阶段定义：\n"
        "- 第1阶段：第2至第4颈椎下缘近于平坦，第3、第4颈椎椎体多呈梯形。\n"
        "- 第2阶段：第2颈椎下缘出现凹陷，第3、第4颈椎椎体多呈梯形。\n"
        "- 第3阶段：第2和第3颈椎下缘出现凹陷，第3、第4颈椎椎体呈梯形或水平长方形。\n"
        "- 第4阶段：第2至第4颈椎下缘均有凹陷，第3、第4颈椎椎体主要呈水平长方形。\n"
        "- 第5阶段：第2至第4颈椎下缘均有凹陷，第3、第4颈椎椎体至少一个接近方形。\n"
        "- 第6阶段：第2至第4颈椎下缘均有凹陷，第3、第4颈椎椎体至少一个呈垂直长方形。\n\n"
        "判定与输出规则：\n"
        "grade_value表示颈椎成熟阶段，只能选择上述一个阶段。按整体形态组合判断，不仅凭一处凹陷或年龄印象判级，不混用其他阶段体系。\n\n"
        "请仅按以下结构输出合法JSON，字段按上述规则填写，不增加额外字段、正文说明或代码围栏：\n"
        "{\n"
        '  "grade_value": "<第1阶段至第6阶段之一>"\n'
        "}"
    )


def build_a42_prompt(case: dict[str, Any]) -> str:
    return (
        "请观察提供的影像，评价图中红色框内的牙齿的牙周影像骨丧失程度。\n\n"
        "采用以下等级定义：\n"
        "- 无吸收：目标牙可可靠判读，未见明确病理性牙周牙槽骨吸收；不把生理性牙槽嵴顶位置当作吸收。\n"
        "- 轻度吸收：病理性骨吸收占根长小于三分之一。\n"
        "- 中度吸收：病理性骨吸收占根长三分之一至三分之二，包含两个边界。\n"
        "- 重度吸收：病理性骨吸收占根长大于三分之二。\n\n"
        "根长以釉牙骨质界至根尖为参照；结合釉牙骨质界、牙槽嵴顶与根尖位置判断骨丧失相对于根长的程度。以该牙近中、远中可可靠判读部位中骨吸收比例较大的一处给出一个等级。\n\n"
        "判定与输出规则：\n"
        "1. grade_value表示目标牙的骨丧失等级，只能选择上述一个等级。\n"
        "2. 影像模糊、目标未显示完整或嵴顶不可辨不等于无吸收。\n"
        "3. 只评价牙周牙槽骨支持，不把根尖周透射影的大小当作牙周骨丧失程度。\n\n"
        "请仅按以下结构输出合法JSON，字段按上述规则填写，不增加额外字段、正文说明或代码围栏：\n"
        "{\n"
        '  "grade_value": "<无吸收、轻度吸收、中度吸收或重度吸收>"\n'
        "}"
    )


def get_a43_target_surfaces(case: dict[str, Any]) -> list[str]:
    for field in case.get("input", {}).get("fields", []):
        if field.get("key") == "target_surfaces":
            raw_surfaces = field.get("value", [])
            if not isinstance(raw_surfaces, list):
                raise ValueError("target_surfaces must be a list")
            return [A43_SURFACE_LABELS.get(str(surface).strip(), str(surface).strip()) for surface in raw_surfaces]
    raise ValueError(f"case has no target_surfaces: {case.get('id')}")


def build_a43_prompt(case: dict[str, Any]) -> str:
    surfaces = get_a43_target_surfaces(case)
    surface_text = "、".join(surfaces)
    return (
        "请观察提供的影像，按下列标准逐一评价图中红色框内的牙齿的指定牙面，判断龋损影像深度。\n\n"
        f"指定牙面（按此顺序作答）：{surface_text}\n\n"
        "采用以下等级定义：\n"
        "- 无龋：指定牙面可可靠判读，影像未见明确龋损征象；仅表示该牙面的影像判断，不等同于排除所有临床龋病。\n"
        "- 浅龋：牙冠龋损透射范围局限于釉质，未明确进入牙本质。\n"
        "- 中龋：龋损透射范围进入牙本质浅层，未达牙本质深层。\n"
        "- 深龋：龋损透射范围达到牙本质深层、接近髓腔。\n\n"
        "牙面词表：近中面、远中面、咬合面、颊／唇面、舌／腭面。只回答指定的牙面。\n"
        "判定与输出规则：\n"
        "1. surface_grades记录各牙面的分级，每个指定牙面恰好一项，按给定顺序输出；target_surface使用对应中文牙面名称，不遗漏或添加牙面。\n"
        "2. 每个牙面独立判断，grade_value只选上述一个等级。同一牙面有多处可分级龋损时按最深处判断；不能把一处龋损的深度复制给所有牙面。\n\n"
        "请仅按以下结构输出合法JSON，字段按上述规则填写，不增加额外字段、正文说明或代码围栏：\n"
        "{\n"
        '  "surface_grades": [\n'
        '    {\n'
        '      "target_surface": "<一个指定牙面的中文名称>",\n'
        '      "grade_value": "<无龋、浅龋、中龋或深龋>"\n'
        '    }\n'
        '  ]\n'
        "}"
    )


def parse_json_object(text: str | None) -> dict[str, Any]:
    if text is None:
        raise ValueError("empty model response")

    stripped = text.strip()
    if not stripped:
        raise ValueError("empty model response")

    candidates = [stripped]
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    candidates.extend(fenced)

    first = stripped.find("{")
    last = stripped.rfind("}")
    if first >= 0 and last > first:
        candidates.append(stripped[first:last + 1])

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
        except Exception as exc:
            last_error = exc
            continue
        if not isinstance(obj, dict):
            last_error = ValueError("parsed JSON is not an object")
            continue
        return {str(key): value for key, value in obj.items()}

    raise ValueError(f"cannot parse JSON object from response: {last_error}")


def parse_a11_answer(text: str | None) -> dict[str, str]:
    obj = parse_json_object(text)
    missing = [key for key in A11_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A11_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")

    parsed = {
        "modality_type": str(obj["modality_type"]).strip(),
        "field_of_view": str(obj["field_of_view"]).strip(),
    }
    if parsed["modality_type"] not in MODALITY_OPTIONS:
        raise ValueError(f"invalid modality_type: {parsed['modality_type']}")
    all_view_options = {
        view
        for options in A11_VIEW_OPTIONS_BY_MODALITY.values()
        for view in options
    }
    if parsed["field_of_view"] not in all_view_options:
        raise ValueError(f"invalid field_of_view: {parsed['field_of_view']}")
    return parsed


def parse_a12_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A12_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A12_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")

    return {
        "coverage_codes": normalize_coverage_codes(obj["coverage_codes"]),
        "quality_grade": normalize_quality_grade(obj["quality_grade"]),
    }


def parse_a13_answer(text: str | None) -> dict[str, str]:
    obj = parse_json_object(text)
    missing = [key for key in A13_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A13_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")

    parsed = {
        "sufficiency": str(obj["sufficiency"]).strip(),
        "minimum_necessary_action": normalize_action_value(obj["minimum_necessary_action"]),
    }
    validate_a13_answer(parsed)
    return parsed


def parse_a21_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A21_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A21_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")

    parsed = {
        "dentition_stage": str(obj["dentition_stage"]).strip(),
    }
    validate_a21_answer(parsed)
    return parsed


def parse_a22_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A22_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A22_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    return {"teeth": normalize_a22_teeth(obj["teeth"])}


def parse_a23_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A23_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A23_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    return {"teeth": normalize_a23_teeth(obj["teeth"])}


def parse_a24_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A24_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A24_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    return {"structures": normalize_a24_structures(obj["structures"])}


def parse_a31_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A31_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A31_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    return {"findings": normalize_a31_findings(obj["findings"])}


def parse_a32_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A32_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A32_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    return {"findings": normalize_a32_findings(obj["findings"])}


def parse_a33_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A33_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A33_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    return {"findings": normalize_a33_findings(obj["findings"])}


def parse_a34_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A34_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A34_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    return {"findings": normalize_a34_findings(obj["findings"])}


def parse_a41_answer(text: str | None) -> dict[str, str]:
    obj = parse_json_object(text)
    missing = [key for key in A41_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A41_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    grade = str(obj["grade_value"]).strip()
    if grade not in A41_GRADE_ALIASES:
        raise ValueError(f"invalid grade_value: {grade}")
    return {"grade_value": A41_GRADE_ALIASES[grade]}


def parse_a42_answer(text: str | None) -> dict[str, str]:
    obj = parse_json_object(text)
    missing = [key for key in A42_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A42_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    grade = str(obj["grade_value"]).strip()
    if grade not in {"无吸收", "轻度吸收", "中度吸收", "重度吸收"}:
        raise ValueError(f"invalid grade_value: {grade}")
    return {"grade_value": grade}


def normalize_a43_surface_grades(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("surface_grades must be a list")
    normalized = []
    for item in value:
        if not isinstance(item, dict) or not {"target_surface", "grade_value"}.issubset(item):
            raise ValueError(f"invalid surface grade item: {item}")
        surface = A43_SURFACE_ALIASES.get(str(item["target_surface"]).strip())
        grade = str(item["grade_value"]).strip()
        if surface is None or grade not in A43_GRADE_OPTIONS:
            raise ValueError(f"invalid surface grade item: {item}")
        normalized.append({"target_surface": surface, "grade_value": grade})
    return normalized


def parse_a43_answer(text: str | None) -> dict[str, Any]:
    obj = parse_json_object(text)
    missing = [key for key in A43_ANSWER_KEYS if key not in obj]
    if missing:
        raise ValueError(f"missing required answer keys: {missing}")
    extra = [key for key in obj if key not in A43_ANSWER_KEYS]
    if extra:
        raise ValueError(f"unexpected answer keys: {extra}")
    raw_grades = obj["surface_grades"]
    if not isinstance(raw_grades, list):
        raise ValueError("surface_grades must be a list")
    for item in raw_grades:
        if not isinstance(item, dict) or set(item) != {"target_surface", "grade_value"}:
            raise ValueError(f"invalid surface grade item: {item}")
    return {"surface_grades": normalize_a43_surface_grades(obj["surface_grades"])}


def normalize_answer(value: str) -> str:
    text = re.sub(r"\s+", "", str(value)).strip()
    text = text.replace("粘", "黏")
    text = text.replace("９０", "90").replace("１８０", "180")
    text = text.replace("°", "").replace("度", "")
    return text


def validate_a11_answer(answer: dict[str, str]) -> None:
    modality = answer["modality_type"]
    if modality not in MODALITY_OPTIONS:
        raise ValueError(f"invalid modality_type: {modality}")

    if answer["field_of_view"] not in A11_VIEW_OPTIONS_BY_MODALITY[modality]:
        raise ValueError(
            f"field_of_view {answer['field_of_view']} is not compatible with modality_type {modality}"
        )


def normalize_coverage_codes(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"coverage_codes must be a list: {value}")
    if not value:
        raise ValueError("coverage_codes must be non-empty")
    if len(value) != 1:
        raise ValueError("coverage_codes must contain exactly one item")

    coverage = []
    for item in value:
        code = str(item).strip()
        if code not in A12_COVERAGE_OPTIONS:
            raise ValueError(f"invalid coverage code: {code}")
        coverage.append(code)
    return coverage


def normalize_quality_grade(value: Any) -> str:
    text = str(value).strip()
    text = A12_QUALITY_LABEL_TO_CODE.get(text, text)
    if text not in A12_QUALITY_CODE_TO_LABEL:
        raise ValueError(f"invalid quality_grade: {value}")
    return text


def validate_a13_answer(answer: dict[str, str]) -> None:
    if answer["sufficiency"] not in SUFFICIENCY_OPTIONS:
        raise ValueError(f"invalid sufficiency: {answer['sufficiency']}")

    action_value = answer["minimum_necessary_action"]
    action_code, _, requested_view = action_value.partition(":")
    if action_code not in ACTION_OPTIONS:
        raise ValueError(f"invalid minimum_necessary_action: {action_value}")
    if action_code == "补充缺失视角":
        allowed_views = set(NON_MUCOSA_VIEW_OPTIONS) | set(VIEW_OPTIONS_BY_MODALITY["黏膜照"])
        if requested_view not in allowed_views:
            raise ValueError(f"invalid requested_view for 补充缺失视角: {requested_view}")


def validate_a21_answer(answer: dict[str, Any]) -> None:
    stage = answer["dentition_stage"]
    if stage not in DENTITION_STAGE_OPTIONS:
        raise ValueError(f"invalid dentition_stage: {stage}")


def normalize_unevaluable_reasons(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"unevaluable_reasons must be a list: {value}")

    reasons = []
    for item in value:
        reason = str(item).strip()
        if reason not in UNEVALUABLE_REASON_OPTIONS:
            raise ValueError(f"invalid unevaluable reason: {reason}")
        reasons.append(reason)
    return sorted(set(reasons), key=UNEVALUABLE_REASON_OPTIONS.index)


def normalize_a22_teeth(value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"teeth must be a list: {value}")

    if not value:
        return []
    if all(isinstance(item, dict) for item in value):
        if all("bbox" not in item and "normalized_bbox" not in item for item in value):
            return sorted(set(normalize_fdi(item.get("fdi")) for item in value))
        if any("bbox" not in item and "normalized_bbox" not in item for item in value):
            raise ValueError("tooth bbox objects must include bbox or normalized_bbox for every item")
        teeth_by_fdi: dict[int, dict[str, Any]] = {}
        for item in value:
            fdi = normalize_fdi(item.get("fdi"))
            bbox_value = item.get("bbox", item.get("normalized_bbox"))
            teeth_by_fdi[fdi] = {
                "fdi": fdi,
                "bbox": normalize_bbox(bbox_value),
            }
        return [teeth_by_fdi[fdi] for fdi in sorted(teeth_by_fdi)]
    if all(not isinstance(item, dict) for item in value):
        return sorted(set(normalize_fdi(item) for item in value))
    raise ValueError("teeth must contain either only FDI integers or only tooth bbox objects")


def normalize_a23_teeth(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"teeth must be a list: {value}")

    teeth_by_fdi: dict[int, dict[str, Any]] = {}
    fdi_order: list[int] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"tooth status item must be an object: {item}")
        if "fdi" not in item or "status" not in item:
            raise ValueError(f"tooth status item must include fdi and status: {item}")

        fdi = normalize_fdi(item.get("fdi"))
        status = normalize_tooth_development_status(item.get("status"))
        if status not in TOOTH_DEVELOPMENT_STATUS_OPTIONS:
            raise ValueError(f"invalid tooth status: {status}")
        if fdi not in teeth_by_fdi:
            fdi_order.append(fdi)
        teeth_by_fdi[fdi] = {"fdi": fdi, "status": status}

    return [teeth_by_fdi[fdi] for fdi in fdi_order]


def normalize_a24_structures(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"structures must be a list: {value}")

    structures: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"structure item must be an object: {item}")
        if "structure_code" not in item or "coordinate" not in item:
            raise ValueError(f"structure item must include structure_code and coordinate: {item}")

        structure_code = normalize_a24_structure_code(item["structure_code"])
        coordinate = normalize_coordinate(item["coordinate"])
        fdi = normalize_fdi(item["fdi"]) if "fdi" in item and item["fdi"] not in (None, "") else None
        key = (structure_code, fdi)
        if key in seen:
            continue
        seen.add(key)

        normalized = {
            "structure_code": structure_code,
            "coordinate": coordinate,
        }
        if fdi is not None:
            normalized["fdi"] = fdi
        structures.append(normalized)
    return structures


def normalize_a31_findings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"findings must be a list: {value}")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or "finding_code" not in item:
            raise ValueError(f"finding item must include finding_code: {item}")
        code = str(item["finding_code"]).strip()
        if code not in A31_FINDING_CODES:
            raise ValueError(f"invalid finding_code: {code}")
        site = item.get("site") if isinstance(item.get("site"), dict) else {}
        if "fdi" in item or "fdi" in site:
            fdi_values = item.get("fdi", site.get("fdi", []))
            fdis = sorted(set(normalize_fdi(fdi) for fdi in fdi_values))
            if not fdis:
                raise ValueError("fdi must be non-empty")
            normalized.append({"finding_code": code, "fdi": fdis})
        elif "bbox" in item or "normalized_bbox" in item:
            normalized.append({"finding_code": code, "bbox": normalize_bbox(item.get("bbox", item.get("normalized_bbox")))})
        else:
            region = item.get("region_code", item.get("region", site))
            if isinstance(region, dict):
                regions = region.get("region_codes", [])
            else:
                regions = region if isinstance(region, list) else [region]
            for region_code in regions:
                region_code = str(region_code).strip()
                if region_code not in A31_REGION_CODES:
                    raise ValueError(f"invalid region_code: {region_code}")
                normalized.append({"finding_code": code, "region_code": region_code})
    return normalized


def normalize_a32_findings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"findings must be a list: {value}")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or "finding_code" not in item:
            raise ValueError(f"finding item must include finding_code: {item}")
        raw_code = str(item["finding_code"]).strip()
        code = A32_FINDING_CODE_ALIASES.get(raw_code, raw_code)
        if code == "其他/待审核":
            code = str(item.get("other_text") or "其他/待审核").strip()
        if not code:
            raise ValueError("finding_code must be non-empty")
        if "bbox" in item or "normalized_bbox" in item:
            normalized.append({"finding_code": code, "bbox": normalize_bbox(item.get("bbox", item.get("normalized_bbox")))})
            continue
        site = item.get("site") if isinstance(item.get("site"), dict) else {}
        regions = item.get("region_code", item.get("region_codes", site.get("region_codes", [])))
        if isinstance(regions, str):
            regions = [regions]
        if not isinstance(regions, list) or not regions:
            raise ValueError("region_code must be a non-empty list")
        cleaned = [str(region).strip() for region in regions]
        if any(region not in A32_REGION_CODES for region in cleaned):
            raise ValueError(f"invalid soft-tissue region_code: {cleaned}")
        normalized.append({
            "finding_code": code,
            "region_code": list(dict.fromkeys(cleaned)),
        })
    return normalized


def normalize_a33_findings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"findings must be a list: {value}")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or "finding_code" not in item:
            raise ValueError(f"finding item must include finding_code: {item}")
        raw_code = str(item["finding_code"]).strip()
        code = A33_FINDING_CODE_ALIASES.get(raw_code, raw_code)
        if code == "其他/待审核":
            code = str(item.get("other_text") or "其他/待审核").strip()
        if not code:
            raise ValueError("finding_code must be non-empty")
        if "bbox" in item or "normalized_bbox" in item:
            normalized.append({"finding_code": code, "bbox": normalize_bbox(item.get("bbox", item.get("normalized_bbox")))})
        elif "fdi" in item:
            fdis = sorted(set(normalize_fdi(fdi) for fdi in item["fdi"]))
            if not fdis:
                raise ValueError("fdi must be non-empty")
            normalized.append({"finding_code": code, "fdi": fdis})
        else:
            site = item.get("site") if isinstance(item.get("site"), dict) else {}
            if site.get("type") == "tooth":
                fdis = sorted(set(normalize_fdi(fdi) for fdi in site.get("fdi", [])))
                if not fdis:
                    raise ValueError("site.fdi must be non-empty")
                normalized.append({"finding_code": code, "fdi": fdis})
                continue
            regions = item.get("region_code", item.get("region_codes", site.get("region_codes", [])))
            if isinstance(regions, str):
                regions = [regions]
            if not isinstance(regions, list) or not regions:
                raise ValueError("region_code must be a non-empty list")
            cleaned = [str(region).strip() for region in regions]
            if any(region not in A33_REGION_CODES for region in cleaned):
                raise ValueError(f"invalid orthodontic region_code: {cleaned}")
            normalized.append({"finding_code": code, "region_code": list(dict.fromkeys(cleaned))})
    return normalized


def normalize_a34_findings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"findings must be a list: {value}")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or "finding_code" not in item:
            raise ValueError(f"finding item must include finding_code: {item}")
        raw_code = str(item["finding_code"]).strip()
        code = A34_FINDING_CODE_ALIASES.get(raw_code, raw_code)
        if code == "其他/待审核":
            code = str(item.get("other_text") or "其他/待审核").strip()
        if not code:
            raise ValueError("finding_code must be non-empty")
        if "bbox" in item or "normalized_bbox" in item:
            normalized.append({"finding_code": code, "bbox": normalize_bbox(item.get("bbox", item.get("normalized_bbox")))})
            continue
        if "fdi" in item:
            fdis = sorted(set(normalize_fdi(fdi) for fdi in item["fdi"]))
            if not fdis:
                raise ValueError("fdi must be non-empty")
            normalized.append({"finding_code": code, "fdi": fdis})
            continue
        site = item.get("site") if isinstance(item.get("site"), dict) else {}
        if site.get("type") == "tooth":
            fdis = sorted(set(normalize_fdi(fdi) for fdi in site.get("fdi", [])))
            if not fdis:
                raise ValueError("site.fdi must be non-empty")
            normalized.append({"finding_code": code, "fdi": fdis})
            continue
        regions = item.get("region_code", item.get("region_codes", site.get("region_codes", [])))
        if isinstance(regions, str):
            regions = [regions]
        if not isinstance(regions, list) or not regions:
            raise ValueError("region_code must be a non-empty list")
        cleaned = [str(region).strip() for region in regions]
        if any(region not in A34_REGION_CODES for region in cleaned):
            raise ValueError(f"invalid treatment-status region_code: {cleaned}")
        normalized.append({"finding_code": code, "region_code": list(dict.fromkeys(cleaned))})
    return normalized


def normalize_a24_structure_code(value: Any) -> str:
    code = str(value).strip()
    code = PERIAPICAL_STRUCTURE_LABEL_TO_CODE.get(code, code)
    return CEPHALOMETRIC_STRUCTURE_ALIASES.get(code, code)


def normalize_tooth_development_status(value: Any) -> str:
    status = str(value).strip()
    return TOOTH_DEVELOPMENT_STATUS_ALIASES.get(status, status)


def normalize_fdi(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError(f"invalid FDI value: {value}")
    try:
        fdi = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid FDI value: {value}") from exc
    if fdi not in VALID_FDI_CODES:
        raise ValueError(f"FDI value out of allowed range: {fdi}")
    return fdi


def normalize_bbox(value: Any) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"bbox must be a four-number list: {value}")
    try:
        left, top, right, bottom = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"bbox values must be numbers: {value}") from exc
    if not (0 <= left <= 1 and 0 <= top <= 1 and 0 <= right <= 1 and 0 <= bottom <= 1):
        raise ValueError(f"bbox values must be normalized to 0-1: {value}")
    if left >= right or top >= bottom:
        raise ValueError(f"invalid bbox boundaries: {value}")
    return [round(left, 6), round(top, 6), round(right, 6), round(bottom, 6)]


def normalize_coordinate(value: Any) -> list[float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"coordinate must be a two-number list: {value}")
    try:
        x, y = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"coordinate values must be numbers: {value}") from exc
    x = min(1.0, max(0.0, x))
    y = min(1.0, max(0.0, y))
    return [round(x, 6), round(y, 6)]


def get_field_value(case: dict[str, Any], key: str) -> Any:
    for item in case.get("input", {}).get("fields", []):
        if item.get("key") == key:
            return item.get("value")
    return None


def extract_a22_reference_fdis(case: dict[str, Any]) -> list[int]:
    for item in case.get("reference_answer", {}).get("fields", []):
        if item.get("key") == "teeth":
            return sorted(normalize_fdi(tooth.get("fdi")) for tooth in item.get("value", []))
    return []


def extract_a23_target_fdis(case: dict[str, Any]) -> list[int]:
    for source_key in ("input", "reference_answer"):
        for item in case.get(source_key, {}).get("fields", []):
            if item.get("key") not in {"target_fdis", "target_teeth", "teeth"}:
                continue
            value = item.get("value", [])
            if not isinstance(value, list):
                continue
            fdis: list[int] = []
            for tooth in value:
                raw_fdi = tooth.get("fdi") if isinstance(tooth, dict) else tooth
                fdi = normalize_fdi(raw_fdi)
                if fdi not in fdis:
                    fdis.append(fdi)
            if fdis:
                return fdis
    if is_counterfactual_case(case):
        return generate_counterfactual_a23_fdis(case)
    return []


def extract_a24_reference_structures(case: dict[str, Any]) -> list[dict[str, Any]]:
    for item in case.get("reference_answer", {}).get("fields", []):
        if item.get("key") == "structures":
            value = item.get("value", [])
            return value if isinstance(value, list) else []
    return []


def extract_a24_cephalometric_structures(case: dict[str, Any]) -> list[str]:
    for item in case.get("input", {}).get("fields", []):
        if item.get("key") != "target_structures":
            continue
        value = item.get("value", [])
        if isinstance(value, list):
            structures = [normalize_a24_structure_code(code) for code in value]
            return list(dict.fromkeys(structures))

    structures = []
    for item in extract_a24_reference_structures(case):
        if not isinstance(item, dict):
            continue
        structure_code = normalize_a24_structure_code(item.get("structure_code"))
        if structure_code not in structures:
            structures.append(structure_code)
    return structures


def extract_a24_periapical_target_fdis(case: dict[str, Any]) -> list[int]:
    for source_key in ("input", "reference_answer"):
        for item in case.get(source_key, {}).get("fields", []):
            if item.get("key") not in {"target_fdis", "target_teeth", "teeth"}:
                continue
            value = item.get("value", [])
            if not isinstance(value, list):
                continue
            fdis: list[int] = []
            for tooth in value:
                raw_fdi = tooth.get("fdi") if isinstance(tooth, dict) else tooth
                fdi = normalize_fdi(raw_fdi)
                if fdi not in fdis:
                    fdis.append(fdi)
            if fdis:
                return sorted(fdis, key=lambda fdi: FDI_LEFT_TO_RIGHT_RANK[fdi])

    fdis = []
    for item in extract_a24_reference_structures(case):
        if not isinstance(item, dict) or "fdi" not in item:
            continue
        fdi = normalize_fdi(item["fdi"])
        if fdi not in fdis:
            fdis.append(fdi)
    return sorted(fdis, key=lambda fdi: FDI_LEFT_TO_RIGHT_RANK[fdi])


def _a24_stable_rng(case: dict[str, Any]) -> random.Random:
    """Create a reproducible per-case RNG for A2.4 target sampling."""
    seed_text = "A2.4|{}|{}".format(
        case.get("id", ""),
        case.get("case_code", ""),
    )
    seed = int.from_bytes(hashlib.sha256(seed_text.encode('utf-8')).digest()[:8], "big")
    return random.Random(seed)


def select_a24_cephalometric_structures(case: dict[str, Any]) -> list[str]:
    """Select four landmarks deterministically, preserving the case list order."""
    structures = extract_a24_cephalometric_structures(case)
    if len(structures) <= 4:
        return structures
    rng = _a24_stable_rng(case)
    indexes = sorted(rng.sample(range(len(structures)), 4))
    return [structures[index] for index in indexes]


def select_a24_periapical_target_fdis(case: dict[str, Any]) -> list[int]:
    """Select one target tooth deterministically from the case's target teeth."""
    fdis = extract_a24_periapical_target_fdis(case)
    if len(fdis) <= 1:
        return fdis
    rng = _a24_stable_rng(case)
    return [fdis[rng.randrange(len(fdis))]]


def extract_a24_periapical_image_fdis(case: dict[str, Any]) -> list[int]:
    for item in case.get("input", {}).get("fields", []):
        if item.get("key") not in {"image_fdis", "visible_fdis", "included_fdis"}:
            continue
        value = item.get("value", [])
        if isinstance(value, list):
            fdis = {normalize_fdi(fdi) for fdi in value}
            return sorted(fdis, key=lambda fdi: FDI_LEFT_TO_RIGHT_RANK[fdi])
    return extract_a24_periapical_target_fdis(case)


def extract_a24_periapical_left_to_right_fdis(case: dict[str, Any]) -> list[int]:
    """Return image FDI values in the fixed dental arch order."""
    return extract_a24_periapical_image_fdis(case)


def is_counterfactual_case(case: dict[str, Any]) -> bool:
    for source_key in ("input", "reference_answer"):
        for item in case.get(source_key, {}).get("fields", []):
            if item.get("key") == "counterfactual" and item.get("value") is True:
                return True
    return False


def generate_counterfactual_a23_fdis(case: dict[str, Any]) -> list[int]:
    seed_source = str(case.get("id") or case.get("input", {}).get("images", [{}])[0].get("path", ""))
    rng = random.Random(seed_source)
    return rng.sample(sorted(VALID_FDI_CODES), 2)


def normalize_action_value(value: Any) -> str:
    if isinstance(value, dict):
        action_code = str(value.get("action_code", "")).strip()
        requested_view = str(value.get("requested_view", "")).strip()
    else:
        action_code = str(value).strip()
        requested_view = ""

    action_code = OLD_ACTION_CODE_TO_LABEL.get(action_code, action_code)
    if action_code == "补充缺失视角":
        return f"{action_code}:{requested_view}"
    return action_code


def format_clinical_purpose(purpose: dict[str, Any]) -> str:
    custom_goal_text = str(purpose.get("custom_goal_text", "")).strip()
    if purpose.get("goal_code") == "OTHER_REVIEW" and custom_goal_text:
        return custom_goal_text

    site = purpose.get("site", {})
    site_text = "、".join(site.get("region_codes", [])) if isinstance(site, dict) else ""
    department_code = purpose.get("department_code", "")
    goal_code = purpose.get("goal_code", "")
    parts = [
        DEPARTMENT_LABELS.get(department_code, department_code),
        GOAL_LABELS.get(goal_code, goal_code),
    ]
    if site_text:
        parts.append(f"部位：{site_text}")
    return "；".join(part for part in parts if part)


def clinical_input_fields(case: dict[str, Any]) -> dict[str, Any]:
    """Keep structured values (including numbers and objects) intact."""
    return {item["key"]: item["value"] for item in case["input"].get("fields", [])}


def clinical_media(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve M identifiers by path, in the actual image sending order."""
    evidence = clinical_input_fields(case).get("evidence_media", [])
    by_path = {item["path"]: item for item in evidence}
    images = case["input"].get("images", [])
    paths = [item["path"] for item in images]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate image paths in clinical case")
    if set(by_path) != set(paths) or len(by_path) != len(evidence):
        raise ValueError("evidence_media must match input.images one to one")
    ordered = [by_path[path] for path in paths]
    ids = [item["evidence_id"] for item in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate evidence_media identifiers")
    return ordered


def build_clinical_prompt(case: dict[str, Any]) -> str:
    """Render the supplied templates from inputs only, never reference answers."""
    code = case["task_code"]
    if code not in CLINICAL_FIELD_KEYS:
        raise ValueError(f"unsupported clinical task: {code}")
    fields = clinical_input_fields(case)
    media = clinical_media(case)
    facts = "\n".join(
        f"[{item['evidence_id']}] {item['text']}" for item in fields.get("clinical_facts", [])
    ) or "未额外提供"
    options = "\n".join(item["diagnosis"] for item in fields.get("diagnosis_options", []))
    replacements = {
        "科室中文名称": DEPARTMENT_LABELS.get(fields.get("department_code"), fields.get("department_code", "未提供")),
        "事实列表": facts,
        "事实列表；未提供时注明未额外提供": facts,
        "所选科室对应的诊断列表": options,
        "本题正确诊断与待排除诊断组成的中文候选列表": options,
        "诊断名称": fields.get("diagnosis", fields.get("target_diagnosis", "未提供")),
        "诊断目标": fields.get("diagnostic_goal", "未提供"),
        "实体名称": fields.get("target_entity", "未提供"),
        "按发送顺序列出的影像M编号": "\n".join(item["evidence_id"] for item in media),
        "性别": fields.get("sex", "未提供"),
        "年龄": fields.get("age", "未提供"),
        "患者资料": fields.get("patient_info", "未额外提供"),
        "主诉": fields.get("chief_complaint", "未提供"),
        "病史": fields.get("history", "未提供"),
        "口腔检查结果": fields.get("clinical_exam", "未提供"),
        "影像检查描述": fields.get("imaging_exam", "未提供"),
        "患者偏好": fields.get("patient_preferences") or "未提供",
    }
    template = (Path(__file__).parent / "prompts" / f"{code}.txt").read_text(encoding="utf-8-sig")

    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in replacements:
            raise ValueError(f"unknown prompt placeholder: {key}")
        return str(replacements[key])

    prompt = re.sub(r"\{\{([^{}]+)\}\}", replace, template).strip()
    # All candidates come from input; favored/excluded labels stay private.
    if code in {"A5.1", "A5.2", "A6.2"} and not options:
        raise ValueError("diagnosis_options must not be empty")
    if code == "A6.1" and fields.get("entity_description"):
        prompt += f"\n\n实体定义或计数说明：{fields['entity_description']}"
    if media:
        prompt += "\n\n影像发送顺序：\n" + "\n".join(
            f"第{i}张：{item['evidence_id']}" for i, item in enumerate(media, 1)
        )
    return prompt


def _clinical_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _clinical_count(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("counts must be non-negative integers")
    return value


def parse_clinical_answer(text: str | None, task_code: str) -> dict[str, Any]:
    obj = parse_json_object(text)
    allowed = set(CLINICAL_FIELD_KEYS[task_code])
    required = allowed - ({"reason"} if task_code == "A5.3" else set())
    if set(obj) - allowed or required - set(obj):
        raise ValueError(f"invalid answer keys for {task_code}: {sorted(obj)}")
    if task_code in {"A5.1", "A5.2", "A6.2"}:
        diagnoses = obj["diagnoses"]
        if not isinstance(diagnoses, list) or not diagnoses:
            raise ValueError("diagnoses must be a non-empty array")
        obj["diagnoses"] = [_clinical_text(item, "diagnosis") for item in diagnoses]
        if len(set(obj["diagnoses"])) != len(diagnoses):
            raise ValueError("duplicate diagnoses")
        obj["reason"] = _clinical_text(obj["reason"], "reason")
        if task_code == "A5.1" and len(obj["reason"]) > 100:
            raise ValueError("A5.1 reason must be at most 100 characters")
        if task_code == "A5.2":
            obj["exclude_reason"] = _clinical_text(obj["exclude_reason"], "exclude_reason")
            if len(obj["exclude_reason"]) > 100 or len(obj["reason"]) > 100:
                raise ValueError("A5.2 reasons must be at most 100 characters each")
        if task_code == "A6.2" and len(obj["reason"]) > 100:
            raise ValueError("A6.2 reason must be at most 100 characters")
    elif task_code == "A5.3":
        if obj["sufficiency"] not in ("充足", "不足"):
            raise ValueError("sufficiency must be 充足 or 不足")
        if obj["sufficiency"] == "充足":
            if "reason" in obj:
                raise ValueError("omit reason when sufficiency is 充足")
        else:
            obj["reason"] = _clinical_text(obj.get("reason"), "reason")
            if len(obj["reason"]) > 100:
                raise ValueError("A5.3 reason must be at most 100 characters")
    elif task_code == "A6.1":
        obj["total"] = _clinical_count(obj["total"])
        if not isinstance(obj["images"], list) or not obj["images"]:
            raise ValueError("images must be a non-empty array")
        ids = []
        for item in obj["images"]:
            if not isinstance(item, dict) or set(item) != {"image", "count"}:
                raise ValueError("each image count requires image and count")
            item["image"] = _clinical_text(item["image"], "image")
            item["count"] = _clinical_count(item["count"])
            ids.append(item["image"])
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate image identifiers")
        counts = [item["count"] for item in obj["images"]]
        if not max(counts) <= obj["total"] <= sum(counts):
            raise ValueError("deduplicated total must be between largest image count and sum")
    elif task_code in {"A6.3", "A7.1"}:
        key = "conditions" if task_code == "A6.3" else "plans"
        if not isinstance(obj[key], list) or not obj[key]:
            raise ValueError(f"{key} must be a non-empty array")
        expected = {"category", "detail"} if key == "conditions" else {"plan"}
        for item in obj[key]:
            if not isinstance(item, dict) or set(item) != expected:
                raise ValueError(f"invalid {key} entry")
            for field in expected:
                item[field] = _clinical_text(item[field], field)
            if key == "conditions" and item["category"] not in ("患者信息", "检查状况", "补充图像"):
                raise ValueError("invalid condition category")
    return obj


def validate_clinical_answer(pred: dict[str, Any], case: dict[str, Any]) -> None:
    """Check answer identifiers against this case, without consulting labels."""
    if "diagnoses" in pred:
        options = {item["diagnosis"] for item in clinical_input_fields(case)["diagnosis_options"]}
        if set(pred["diagnoses"]) - options:
            raise ValueError("diagnoses contain names outside input options")
    if case["task_code"] == "A6.1":
        ids = [item["evidence_id"] for item in clinical_media(case)]
        if [item["image"] for item in pred["images"]] != ids:
            raise ValueError("image counts must match all input M identifiers in sending order")


def clinical_reference_answer(case: dict[str, Any]) -> dict[str, Any]:
    """Adapt native annotations to prompt output names; never used in prompts."""
    fields = {item["key"]: item["value"] for item in case["reference_answer"]["fields"]}
    code = case["task_code"]
    if code in {"A5.1", "A5.2", "A6.2"}:
        options = {item["option_id"]: item["diagnosis"] for item in clinical_input_fields(case)["diagnosis_options"]}
        if code == "A5.2":
            entries = fields["differential_diagnoses"]
            return {
                "diagnoses": [options[item["option_id"]] for item in entries if item["role"] == "favored"],
                "reason": "；".join(item["reason"] for item in entries if item["role"] == "favored"),
                "exclude_reason": "；".join(f"{options[item['option_id']]}：{item['reason']}" for item in entries if item["role"] == "excluded"),
            }
        return {"diagnoses": [options[key] for key in fields["selected_option_ids"]], "reason": fields["diagnostic_reason"]}
    if code == "A6.1":
        counts = {item["evidence_id"]: item["count"] for item in fields["image_counts"]}
        return {"total": fields["total_count"], "images": [
            {"image": item["evidence_id"], "count": counts[item["evidence_id"]]} for item in clinical_media(case)
        ]}
    if code == "A6.3":
        categories = {"patient_information": "患者信息", "examinations": "检查状况", "additional_images": "补充图像"}
        return {"conditions": [{"category": categories[item["category"]], "detail": item["detail"]} for item in fields["required_conditions"]]}
    if code == "A7.1":
        return {"plans": fields["treatment_plans"]}
    # supported/not_supported does not establish sufficient/insufficient.
    return fields


def build_clinical_mock_response(case: dict[str, Any]) -> str:
    """Synthetic format examples for dry-run, not clinical ground truth."""
    code = case["task_code"]
    if code in {"A5.1", "A5.2", "A6.2"}:
        response = {"diagnoses": [clinical_input_fields(case)["diagnosis_options"][0]["diagnosis"]], "reason": "仅用于验证输出格式。"}
        if code == "A5.2":
            response["exclude_reason"] = "仅用于验证输出格式。"
    elif code == "A5.3":
        response = {"sufficiency": "不足", "reason": "仅用于验证输出格式。"}
    elif code == "A6.1":
        response = {"total": 0, "images": [{"image": item["evidence_id"], "count": 0} for item in clinical_media(case)]}
    elif code == "A6.3":
        response = {"conditions": [{"category": "患者信息", "detail": "仅用于验证输出格式。"}]}
    else:
        response = {"plans": [{"plan": "仅用于验证输出格式。"}]}
    return json.dumps(response, ensure_ascii=False)

