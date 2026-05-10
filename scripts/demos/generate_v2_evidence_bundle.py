from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data" / "raw" / "demo_evidence" / "full_contract_breach"


@dataclass(frozen=True)
class DemoDocument:
    evidence_id: str
    filename: str
    title: str
    note: str
    paragraphs: tuple[str, ...]
    rows: tuple[tuple[str, str], ...] = ()


def register_fonts() -> tuple[str, str]:
    regular = Path("C:/Windows/Fonts/arial.ttf")
    bold = Path("C:/Windows/Fonts/arialbd.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("ArialUnicode", str(regular)))
        pdfmetrics.registerFont(TTFont("ArialUnicode-Bold", str(bold)))
        return "ArialUnicode", "ArialUnicode-Bold"
    return "Helvetica", "Helvetica-Bold"


def build_styles() -> dict[str, ParagraphStyle]:
    font_name, bold_font_name = register_fonts()
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DemoTitle",
            parent=styles["Title"],
            fontName=bold_font_name,
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "DemoSubtitle",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=12,
        ),
        "body": ParagraphStyle(
            "DemoBody",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=11,
            leading=16,
            spaceAfter=8,
        ),
        "label": ParagraphStyle(
            "DemoLabel",
            parent=styles["BodyText"],
            fontName=bold_font_name,
            fontSize=10,
            leading=14,
        ),
    }


def demo_documents() -> list[DemoDocument]:
    return [
        DemoDocument(
            evidence_id="EVID_001",
            filename="EVID_001_hop_dong_mua_ban_xe_may.pdf",
            title="HỢP ĐỒNG MUA BÁN XE MÁY",
            note="Hợp đồng ghi rõ giá, khoản trả trước, hạn giao và điều kiện thanh toán phần còn lại.",
            paragraphs=(
                "Bên bán: Ông Nguyễn Văn A. Bên mua: Ông Trần Văn B.",
                "Tài sản mua bán: xe máy Honda SH Mode, màu trắng, số khung mô phỏng RLHJF5800PZ000001.",
                "Giá mua bán: 40.000.000 đồng. Bên mua thanh toán trước 70% giá trị hợp đồng vào ngày ký.",
                "Phần còn lại 30% được thanh toán ngay sau khi bên bán bàn giao xe và giấy tờ kèm theo.",
                "Thời hạn bàn giao xe: chậm nhất ngày 12/03/2026 tại nơi cư trú của bên mua.",
                "Hợp đồng này không ghi điều kiện bên mua phải thanh toán đủ 100% trước khi bên bán giao xe.",
            ),
            rows=(
                ("Ngày ký", "05/03/2026"),
                ("Giá trị hợp đồng", "40.000.000 đồng"),
                ("Đã thanh toán khi ký", "28.000.000 đồng"),
                ("Hạn giao tài sản", "12/03/2026"),
            ),
        ),
        DemoDocument(
            evidence_id="EVID_002",
            filename="EVID_002_xac_nhan_chuyen_khoan.pdf",
            title="XÁC NHẬN CHUYỂN KHOẢN",
            note="Chứng từ thể hiện bên mua đã chuyển 28.000.000 đồng cho bên bán.",
            paragraphs=(
                "Ngân hàng mô phỏng xác nhận giao dịch chuyển khoản ngày 05/03/2026.",
                "Người chuyển: Trần Văn B. Người nhận: Nguyễn Văn A.",
                "Số tiền: 28.000.000 đồng. Nội dung: thanh toán trước 70% hợp đồng mua bán xe máy ngày 05/03/2026.",
                "Trạng thái giao dịch: thành công.",
            ),
            rows=(
                ("Mã giao dịch", "FT2603050001"),
                ("Ngày giao dịch", "05/03/2026"),
                ("Số tiền", "28.000.000 đồng"),
                ("Nội dung", "Thanh toán trước 70% hợp đồng mua bán xe máy"),
            ),
        ),
        DemoDocument(
            evidence_id="EVID_003",
            filename="EVID_003_bien_ban_xac_nhan_chua_giao_xe.pdf",
            title="BIÊN BẢN XÁC NHẬN CHƯA GIAO XE",
            note="Biên bản xác nhận sau hạn giao, xe vẫn chưa được bàn giao cho bên mua.",
            paragraphs=(
                "Lập lúc 19 giờ 30 phút ngày 13/03/2026 giữa ông Nguyễn Văn A và ông Trần Văn B.",
                "Hai bên xác nhận đến ngày 13/03/2026, bên bán chưa giao xe Honda SH Mode theo hợp đồng ngày 05/03/2026.",
                "Bên bán xác nhận đã nhận 28.000.000 đồng từ bên mua và chưa hoàn trả khoản tiền này.",
                "Bên bán chưa xuất trình tài liệu thể hiện bên mua phải thanh toán đủ 100% trước khi giao xe.",
                "Biên bản được lập thành hai bản, mỗi bên giữ một bản.",
            ),
            rows=(
                ("Ngày lập", "13/03/2026"),
                ("Tình trạng", "Chưa giao xe"),
                ("Khoản tiền đã nhận", "28.000.000 đồng"),
                ("Phản đối nội dung", "Không ghi nhận phản đối tại thời điểm lập biên bản"),
            ),
        ),
        DemoDocument(
            evidence_id="EVID_004",
            filename="EVID_004_thong_bao_khac_phuc_vi_pham.pdf",
            title="THÔNG BÁO KHẮC PHỤC VI PHẠM HỢP ĐỒNG",
            note="Thông báo yêu cầu bên bán giao xe hoặc hoàn lại khoản đã nhận sau khi quá hạn.",
            paragraphs=(
                "Ngày 14/03/2026, ông Trần Văn B gửi thông báo cho ông Nguyễn Văn A.",
                "Nội dung thông báo: bên bán đã quá hạn giao xe theo hợp đồng ngày 05/03/2026.",
                "Bên mua đề nghị bên bán giao xe trong vòng 03 ngày hoặc hoàn lại 28.000.000 đồng đã nhận.",
                "Thông báo cũng ghi nhận bên mua sẽ bảo lưu quyền yêu cầu chi phí phát sinh có chứng từ.",
            ),
            rows=(
                ("Ngày thông báo", "14/03/2026"),
                ("Thời hạn khắc phục", "03 ngày"),
                ("Số tiền yêu cầu hoàn lại nếu không giao", "28.000.000 đồng"),
                ("Hình thức gửi", "Email và bản in giao trực tiếp"),
            ),
        ),
        DemoDocument(
            evidence_id="EVID_005",
            filename="EVID_005_chung_tu_chi_phi_phat_sinh.pdf",
            title="CHỨNG TỪ CHI PHÍ PHÁT SINH",
            note="Chứng từ mô phỏng khoản chi phí đi lại phát sinh do chưa nhận được xe đúng hạn.",
            paragraphs=(
                "Bảng kê chi phí đi lại phát sinh trong giai đoạn 13/03/2026 đến 17/03/2026.",
                "Tổng chi phí có hóa đơn mô phỏng: 1.200.000 đồng.",
                "Các khoản chi này được ghi nhận riêng để đánh giá mức bồi thường, không thay thế chứng cứ về nghĩa vụ giao tài sản.",
            ),
            rows=(
                ("13/03/2026", "Taxi đi làm: 240.000 đồng"),
                ("14/03/2026", "Taxi đi làm: 240.000 đồng"),
                ("15/03/2026", "Taxi đi làm: 240.000 đồng"),
                ("16/03/2026", "Taxi đi làm: 240.000 đồng"),
                ("17/03/2026", "Taxi đi làm: 240.000 đồng"),
            ),
        ),
    ]


def render_pdf(document: DemoDocument, output_path: Path) -> None:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=document.title,
        author="AI Courtroom Harness Demo",
    )
    story = [
        Paragraph(document.title, styles["title"]),
        Paragraph("Tài liệu mô phỏng phục vụ demo, không phải văn kiện pháp lý thật.", styles["subtitle"]),
    ]
    for paragraph in document.paragraphs:
        story.append(Paragraph(paragraph, styles["body"]))
    if document.rows:
        table_data = [[Paragraph("Mục", styles["label"]), Paragraph("Nội dung", styles["label"])]]
        table_data.extend(
            [Paragraph(label, styles["body"]), Paragraph(value, styles["body"])]
            for label, value in document.rows
        )
        table = Table(table_data, colWidths=[45 * mm, 105 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f3f5")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8c8c8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend([Spacer(1, 6), table])
    story.append(Spacer(1, 18))
    story.append(Paragraph("Xác nhận mô phỏng: các bên ký tên trên bản lưu hồ sơ.", styles["body"]))
    doc.build(story)


def build_bundle(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    documents = demo_documents()
    manifest = {
        "bundle_id": "full_contract_breach",
        "title": "Tranh chấp hợp đồng mua bán xe máy - bộ chứng cứ đầy đủ",
        "narrative": (
            "Hồ sơ mô phỏng gồm hợp đồng mua bán xe máy ngày 05/03/2026, xác nhận chuyển khoản, "
            "biên bản lập sau hạn bàn giao, thông báo khắc phục và bảng kê chi phí phát sinh. "
            "Các tài liệu được dùng để kiểm tra nghĩa vụ giao tài sản, điều kiện thanh toán phần còn lại "
            "và phạm vi chi phí có chứng từ."
        ),
        "documents": [],
    }
    for document in documents:
        output_path = output_dir / document.filename
        render_pdf(document, output_path)
        manifest["documents"].append(
            {
                "evidence_id": document.evidence_id,
                "filename": document.filename,
                "path": str(output_path),
                "title": document.title,
                "note": document.note,
            }
        )
    manifest_path = output_dir / "manifest.json"
    manifest["manifest_path"] = str(manifest_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the V2 full-trial demo evidence PDF bundle.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated PDFs and manifest.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_bundle(args.output_dir)
    json.dump(manifest, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
