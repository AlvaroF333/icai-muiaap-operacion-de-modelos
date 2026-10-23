"""Generate student-facing assignment handouts for Operación de Modelos.

The PDFs deliberately keep the same compact academic handout shape across
weeks: brief, numbered tasks; explicit evidence; an acceptance checklist; and
the command that proves the work. The source of truth for the exercise itself
remains in each week's ``modules`` directory.
"""

from __future__ import annotations

import argparse
import html
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "assignments"
LOGO = ROOT / "assets" / "comillas_logo.jpg"

INK = colors.HexColor("#18212B")
MUTED = colors.HexColor("#5C6873")
ACCENT = colors.HexColor("#8C2438")
ACCENT_DARK = colors.HexColor("#641A2A")
GOLD = colors.HexColor("#C7A44A")
PALE = colors.HexColor("#F4F1EC")
PALE_BLUE = colors.HexColor("#EEF3F5")
GRID = colors.HexColor("#D8DDE0")
WHITE = colors.white


@dataclass(frozen=True)
class Assignment:
    week: int
    class_number: int
    title: str
    subtitle: str
    duration: str
    modality: str
    prerequisites: str
    goal: str
    context: list[str]
    materials: list[str]
    tasks: list[tuple[str, str]]
    deliverables: list[tuple[str, str]]
    acceptance: list[str]
    rubric: list[tuple[str, str]]
    commands: list[str]
    notes: list[str]
    source_paths: list[str]
    task_snippets: dict[int, tuple[str, str]] = field(default_factory=dict)


styles = getSampleStyleSheet()
BODY = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=9.2,
    leading=13.2,
    textColor=INK,
    spaceAfter=5,
)
BODY_SMALL = ParagraphStyle(
    "BodySmall",
    parent=BODY,
    fontSize=8.1,
    leading=11.1,
    textColor=MUTED,
)
REFERENCE = ParagraphStyle(
    "Reference",
    parent=BODY_SMALL,
    fontSize=7.1,
    leading=8.5,
    spaceBefore=0,
    spaceAfter=0,
)
REFERENCE_HEADING = ParagraphStyle(
    "ReferenceHeading",
    parent=REFERENCE,
    fontName="Helvetica-Bold",
    fontSize=8.1,
    leading=9,
    textColor=ACCENT_DARK,
    spaceBefore=2,
    spaceAfter=2,
)
KICKER = ParagraphStyle(
    "Kicker",
    parent=BODY,
    fontName="Helvetica-Bold",
    fontSize=8.2,
    leading=10,
    textColor=ACCENT,
    tracking=1.2,
    spaceAfter=4,
)
TITLE = ParagraphStyle(
    "AssignmentTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=25,
    textColor=INK,
    spaceAfter=6,
)
SUBTITLE = ParagraphStyle(
    "AssignmentSubtitle",
    parent=BODY,
    fontSize=11.5,
    leading=15,
    textColor=MUTED,
    spaceAfter=11,
)
H1 = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=12.5,
    leading=15,
    textColor=ACCENT_DARK,
    spaceBefore=9,
    spaceAfter=5,
    keepWithNext=True,
)
H2 = ParagraphStyle(
    "Subsection",
    parent=styles["Heading3"],
    fontName="Helvetica-Bold",
    fontSize=9.8,
    leading=12,
    textColor=INK,
    spaceBefore=5,
    spaceAfter=3,
    keepWithNext=True,
)
TASK = ParagraphStyle(
    "Task",
    parent=BODY,
    leftIndent=0,
    firstLineIndent=0,
    spaceAfter=6,
)
WEEK_TWO_BODY = ParagraphStyle(
    "WeekTwoBody",
    parent=BODY,
    fontSize=8.2,
    leading=10.3,
    spaceAfter=3,
)
WEEK_TWO_H1 = ParagraphStyle(
    "WeekTwoSection",
    parent=H1,
    fontSize=10.8,
    leading=12,
    spaceBefore=3,
    spaceAfter=1,
)
WEEK_TWO_TASK = ParagraphStyle(
    "WeekTwoTask",
    parent=WEEK_TWO_BODY,
    spaceAfter=3,
)
TABLE_HEAD = ParagraphStyle(
    "TableHead",
    parent=BODY_SMALL,
    fontName="Helvetica-Bold",
    textColor=WHITE,
    fontSize=7.8,
    leading=9.5,
)
TABLE_CELL = ParagraphStyle(
    "TableCell",
    parent=BODY_SMALL,
    fontSize=7.8,
    leading=10.2,
    textColor=INK,
)
CODE = ParagraphStyle(
    "Code",
    parent=BODY_SMALL,
    fontName="Courier",
    fontSize=7.2,
    leading=9.2,
    textColor=INK,
)
SNIPPET_LABEL = ParagraphStyle(
    "SnippetLabel",
    parent=BODY_SMALL,
    fontName="Helvetica-Bold",
    fontSize=6.8,
    leading=8,
    textColor=ACCENT_DARK,
    spaceAfter=0,
)
SNIPPET_CODE = ParagraphStyle(
    "SnippetCode",
    parent=CODE,
    fontSize=6.5,
    leading=7.4,
    textColor=INK,
)
WEEK_TWO_CODE = ParagraphStyle(
    "WeekTwoCode",
    parent=CODE,
    fontSize=6.6,
    leading=7.7,
)
CALLOUT = ParagraphStyle(
    "Callout",
    parent=BODY,
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=12.5,
    textColor=ACCENT_DARK,
    spaceAfter=0,
)
CENTER_SMALL = ParagraphStyle(
    "CenterSmall",
    parent=BODY_SMALL,
    alignment=TA_CENTER,
)


def text(value: str) -> str:
    """Escape plain text for a ReportLab Paragraph."""

    return html.escape(value).replace("\n", "<br/>")


def p(value: str, style: ParagraphStyle = BODY) -> Paragraph:
    return Paragraph(text(value), style)


def markup(value: str, style: ParagraphStyle = BODY) -> Paragraph:
    """Use only for controlled, local markup such as a bold label."""

    return Paragraph(value, style)


def section(title: str, style: ParagraphStyle = H1) -> list[Flowable]:
    return [Paragraph(text(title), style)]


def snippet_block(label: str, source: str) -> Table:
    block = Table(
        [[p(label, SNIPPET_LABEL)], [Preformatted(source.rstrip(), SNIPPET_CODE)]],
        colWidths=[170 * mm],
        hAlign="LEFT",
    )
    block.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.45, GRID),
                ("LINEBELOW", (0, 0), (-1, 0), 0.35, GRID),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return block


def numbered(
    items: Iterable[tuple[str, str]],
    task_snippets: dict[int, tuple[str, str]] | None = None,
    task_style: ParagraphStyle = TASK,
) -> list[Flowable]:
    flowables: list[Flowable] = []
    snippets = task_snippets or {}
    for number, (title, body) in enumerate(items, start=1):
        task_paragraph = markup(
            f'<font color="{ACCENT.hexval()}"><b>{number:02d}</b></font> '
            f"<b>{html.escape(title)}</b> - {html.escape(body)}",
            task_style,
        )
        if number in snippets:
            label, source = snippets[number]
            flowables.append(
                KeepTogether(
                    [task_paragraph, snippet_block(label, source), Spacer(1, 2)]
                )
            )
        else:
            flowables.append(task_paragraph)
    return flowables


def checklist(
    items: Iterable[str], style: ParagraphStyle = BODY
) -> list[Flowable]:
    return [
        markup(
            f'<font color="{ACCENT.hexval()}">[ ]</font> {html.escape(item)}',
            style,
        )
        for item in items
    ]


def make_table(
    headers: list[str],
    rows: list[tuple[str, ...]],
    widths: list[float] | None = None,
    compact: bool = False,
) -> Table:
    data = [[Paragraph(text(header), TABLE_HEAD) for header in headers]]
    data.extend(
        [[Paragraph(text(cell), TABLE_CELL) for cell in row] for row in rows]
    )
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    vertical_padding = 3 if compact else 5
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE_BLUE]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), vertical_padding),
                ("BOTTOMPADDING", (0, 0), (-1, -1), vertical_padding),
            ]
        )
    )
    return table


def callout(label: str, body: str) -> Table:
    box = Table(
        [[markup(f"<b>{html.escape(label)}</b><br/>{html.escape(body)}", CALLOUT)]],
        colWidths=[170 * mm],
    )
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE),
                ("BOX", (0, 0), (-1, -1), 0.7, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return box


def code_block(
    commands: list[str], style: ParagraphStyle = CODE
) -> Preformatted:
    return Preformatted("\n\n".join(commands), style)


def header_footer(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, height - 18 * mm, width - doc.rightMargin, height - 18 * mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(ACCENT_DARK)
    canvas.drawString(doc.leftMargin, height - 14 * mm, "OPERACION DE MODELOS")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(
        width - doc.rightMargin,
        height - 14 * mm,
        f"MUIAAp  |  semana {doc.assignment.week:02d}  |  clase {doc.assignment.class_number}",
    )
    canvas.setStrokeColor(GRID)
    canvas.line(doc.leftMargin, 15 * mm, width - doc.rightMargin, 15 * mm)
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 10.5 * mm, "Comillas ICAI  |  Material de trabajo")
    canvas.drawRightString(width - doc.rightMargin, 10.5 * mm, f"{canvas.getPageNumber():02d}")
    canvas.restoreState()


def title_block(assignment: Assignment) -> list[Flowable]:
    logo = Image(str(LOGO), width=62 * mm, height=62 * mm * 187 / 710)
    logo.hAlign = "LEFT"
    meta = make_table(
        ["DURACION", "MODALIDAD", "PREREQUISITOS"],
        [(assignment.duration, assignment.modality, assignment.prerequisites)],
        widths=[43 * mm, 48 * mm, 79 * mm],
        compact=assignment.week in {2, 7, 9},
    )
    return [
        logo,
        Spacer(1, 4),
        Paragraph(
            text(f"ASSIGNMENT {assignment.week}.{assignment.class_number}"),
            KICKER,
        ),
        Paragraph(text(assignment.title), TITLE),
        Paragraph(text(assignment.subtitle), SUBTITLE),
        meta,
        Spacer(1, 8),
    ]


def build_story(assignment: Assignment) -> list[Flowable]:
    uses_compact_layout = assignment.week in {2, 7, 9}
    body_style = WEEK_TWO_BODY if uses_compact_layout else BODY
    section_style = WEEK_TWO_H1 if uses_compact_layout else H1
    task_style = WEEK_TWO_TASK if uses_compact_layout else TASK
    story: list[Flowable] = []
    story.extend(title_block(assignment))
    story.extend(section("1. Encargo", section_style))
    story.append(p(assignment.goal, body_style))
    story.append(callout("Regla de continuidad", assignment.context[0]))
    story.append(Spacer(1, 2 if uses_compact_layout else 5))

    story.extend(section("2. Punto de partida", section_style))
    story.extend([p(f"- {item}", body_style) for item in assignment.context[1:]])
    story.extend(section("3. Material que recibes", section_style))
    story.extend([p(f"- {item}", body_style) for item in assignment.materials])

    story.extend(section("4. Tareas", section_style))
    story.extend(
        numbered(assignment.tasks, assignment.task_snippets, task_style)
    )

    story.extend(section("5. Entrega", section_style))
    story.append(
        make_table(
            ["Evidencia", "Que debe permitir comprobar"],
            assignment.deliverables,
            widths=[52 * mm, 118 * mm],
            compact=uses_compact_layout,
        )
    )
    story.append(Spacer(1, 2 if uses_compact_layout else 7))

    acceptance_section = [
        *section("6. Criterios de aceptacion", section_style),
        *checklist(assignment.acceptance, body_style),
    ]
    if uses_compact_layout:
        story.append(KeepTogether(acceptance_section))
    else:
        story.extend(acceptance_section)

    story.extend(section("7. Rubrica orientativa", section_style))
    story.append(
        make_table(
            ["Criterio", "Puntos"],
            assignment.rubric,
            widths=[145 * mm, 25 * mm],
            compact=uses_compact_layout,
        )
    )

    story.extend(section("8. Comprobacion", section_style))
    code_style = WEEK_TWO_CODE if uses_compact_layout else CODE
    story.append(code_block(assignment.commands, code_style))
    story.append(Spacer(1, 0 if uses_compact_layout else 6))

    story.extend(section("9. Notas y limites", section_style))
    story.extend([p(f"- {item}", body_style) for item in assignment.notes])
    story.extend(section("Referencia en el repositorio", REFERENCE_HEADING))
    story.extend([p(path, REFERENCE) for path in assignment.source_paths])
    return story


def assignment(
    week: int,
    class_number: int,
    title: str,
    subtitle: str,
    duration: str,
    modality: str,
    prerequisites: str,
    goal: str,
    context: list[str],
    materials: list[str],
    tasks: list[tuple[str, str]],
    deliverables: list[tuple[str, str]],
    acceptance: list[str],
    rubric: list[tuple[str, str]],
    commands: list[str],
    notes: list[str],
    source_paths: list[str],
    task_snippets: dict[int, tuple[str, str]] | None = None,
) -> Assignment:
    return Assignment(
        week=week,
        class_number=class_number,
        title=title,
        subtitle=subtitle,
        duration=duration,
        modality=modality,
        prerequisites=prerequisites,
        goal=goal,
        context=context,
        materials=materials,
        tasks=tasks,
        deliverables=deliverables,
        acceptance=acceptance,
        rubric=rubric,
        commands=commands,
        notes=notes,
        source_paths=source_paths,
        task_snippets=task_snippets or {},
    )


ASSIGNMENTS = [
    assignment(
        1,
        1,
        "Configuracion inicial del entorno",
        "Herramientas y accesos para S1-S7; Docker preparado para el bloque posterior",
        "90 min; Docker no bloqueante",
        "Individual",
        "Ordenador personal, internet y permisos de instalacion",
        (
            "Preparar y verificar las herramientas y accesos necesarios para S1-S7: "
            "uv con Python 3.12, Git, GitHub, un editor con soporte para "
            "notebooks, Databricks Free Edition, curl y Postman. Revisar ademas Docker "
            "con Compose para anticipar el bloque posterior, sin que condicione "
            "esta entrega."
        ),
        [
            (
                "Esta practica es de puesta a punto: no exige analizar un notebook "
                "ni entregar una ficha de riesgos."
            ),
            (
                "Si una herramienta ya esta instalada, conserva la instalacion y "
                "verifica su version."
            ),
            (
                "En Windows, Git Bash se instala con Git for Windows; en macOS y "
                "Linux se usa la terminal del sistema."
            ),
            (
                "En Databricks selecciona Free Edition, no Free Trial, y no "
                "introduzcas datos de pago."
            ),
            (
                "Postman Desktop es la opcion recomendada; Postman Web necesita "
                "Desktop Agent para acceder a servicios en localhost."
            ),
            (
                "Para S7 verifica curl; en Windows usa curl.exe para evitar el alias "
                "de PowerShell."
            ),
            (
                "Docker y Compose son preparacion anticipada no bloqueante para "
                "esta entrega."
            ),
        ],
        [
            "Documentacion oficial de uv y Python administrado con uv",
            "Instalador oficial de Git; Git for Windows incluye Git Bash",
            "Cuenta GitHub y acceso al repositorio de la asignatura",
            "Pagina oficial de alta de Databricks Free Edition",
            "Navegador actualizado y editor con soporte Python/Jupyter; VS Code es la opcion recomendada",
            "curl del sistema y aplicacion de escritorio Postman o acceso a Postman Web",
            "Documentacion de Docker Desktop o Docker Engine y del plugin Compose",
        ],
        [
            (
                "Comprueba el equipo",
                (
                    "Anota sistema operativo y arquitectura. Confirma que dispones de "
                    "un navegador actualizado, un editor de codigo y permisos para "
                    "instalar software."
                ),
            ),
            (
                "Instala uv y Python",
                (
                    "Instala uv y prepara Python 3.12 administrado con uv. Verifica "
                    "ambos desde una terminal nueva."
                ),
            ),
            (
                "Prepara Git",
                (
                    "Instala Git y, en Windows, Git Bash. Configura user.name y "
                    "user.email con la identidad que usaras en la asignatura. En "
                    "Windows verifica tambien uv y Git dentro de Git Bash. Enmascara "
                    "el correo en la evidencia."
                ),
            ),
            (
                "Verifica GitHub",
                (
                    "Inicia sesion y confirma que puedes abrir el repositorio de la "
                    "asignatura y crear un fork. No compartas tokens ni credenciales."
                ),
            ),
            (
                "Prepara editor y clientes HTTP",
                (
                    "Configura un editor que abra Python, TOML, Markdown y notebooks. "
                    "Si usas VS Code, instala las extensiones Python y Jupyter. Verifica "
                    "curl (curl.exe en Windows) y envia un GET con Postman."
                ),
            ),
            (
                "Verifica Databricks",
                (
                    "Crea el workspace Free Edition, importa semana1 como Git Folder, "
                    "conecta compute serverless y ejecuta la celda inicial de la "
                    "practica hasta leer semana1/data/raw/WineQT.csv."
                ),
            ),
            (
                "Anticipa Docker y Compose",
                (
                    "Comprueba la compatibilidad del equipo y anota un estado: "
                    "verificado, pendiente o bloqueado. Si lo instalas, verifica Docker "
                    "Engine y Compose. La instalacion no bloquea S1.1."
                ),
            ),
            (
                "Prepara la evidencia",
                (
                    "Resume versiones, accesos y estado de Docker. Si algo falla, "
                    "incluye comando, error y siguiente accion, sin datos personales."
                ),
            ),
        ],
        [
            (
                "Entorno S1-S7",
                (
                    "Sistema operativo; versiones de uv, Python, Git y Bash cuando "
                    "aplique; navegador, editor, curl y Postman disponibles."
                ),
            ),
            (
                "Git y GitHub",
                (
                    "Identidad Git configurada con correo enmascarado, acceso al "
                    "repositorio y posibilidad de crear un fork."
                ),
            ),
            (
                "Databricks",
                (
                    "Acceso a Free Edition y smoke test del Git Folder, compute y "
                    "dataset, sin credenciales ni datos de pago."
                ),
            ),
            (
                "Docker posterior",
                (
                    "Estado verificado, pendiente o bloqueado; versiones de Docker y "
                    "Compose solo si ya estan instalados."
                ),
            ),
            (
                "Incidencias",
                (
                    "Mensaje de error, paso intentado y siguiente accion; no basta con "
                    "indicar que no funciona."
                ),
            ),
        ],
        [
            "uv --version devuelve una version y el comando funciona en una terminal nueva.",
            "Python 3.12 esta disponible y administrado con uv.",
            "git --version funciona; en Windows Git Bash abre y ejecuta bash --version.",
            "Git contiene user.name y user.email, y la evidencia no muestra el correo completo.",
            "La cuenta GitHub permite acceder al repositorio y crear un fork.",
            "Databricks abre el Git Folder y ejecuta la comprobacion inicial con compute serverless.",
            "El editor abre codigo y notebooks; curl y Postman realizan una peticion local.",
            "Docker figura como verificado, pendiente o bloqueado; no condiciona la entrega.",
            "No se entregan contrasenas, tokens, correos completos ni datos de pago.",
        ],
        [
            ("uv y Python 3.12", "2"),
            ("Git, GitHub e identidad", "2"),
            ("Databricks y smoke test", "3"),
            ("Editor, notebooks y clientes HTTP", "2"),
            ("Evidencia y seguridad", "1"),
        ],
        [
            "Ejecutar uv --version.",
            "Ejecutar uv python install 3.12 y uv run --python 3.12 python --version.",
            "Ejecutar git --version.",
            "Ejecutar git config --global --get user.name y git config --global --get user.email.",
            "En Windows, abrir Git Bash y ejecutar bash --version, git --version y uv --version.",
            "Abrir el repositorio en GitHub y ejecutar git ls-remote https://github.com/ssillerom/icai-muiaap-operacion-de-modelos.git.",
            "Ejecutar curl.exe --version en Windows o curl --version en macOS y Linux.",
            "En Postman, enviar GET https://postman-echo.com/get y comprobar el estado 200.",
            "En Databricks, abrir el Git Folder y ejecutar la celda inicial de la practica.",
            "Opcional: ejecutar docker --version, docker compose version y docker run --rm hello-world.",
        ],
        [
            "No instales globalmente MLflow, Pydantic, Pytest, Ruff, Streamlit, Gradio, Requests ni FastAPI: se gestionaran con uv o dentro de Databricks.",
            "Docker y Compose se comprobaran de nuevo antes del bloque de contenedores; no instalarlos ahora no resta puntuacion.",
            "La cuenta Postman solo es necesaria si se comparte un workspace; no necesitas Docker Hub, Databricks CLI ni Node.js para S1-S7.",
            "Jupyter local solo es necesario si ejecutaras los notebooks fuera de Databricks; sus paquetes deben instalarse con uv en el proyecto.",
            "En Windows, usa una ruta corta de trabajo, por ejemplo C:/src/operacion-modelos, para evitar limites de longitud.",
            "No selecciones Free Trial ni introduzcas tarjeta para esta asignatura.",
            "No compartas credenciales ni capturas con informacion personal visible.",
        ],
        [
            "uv: docs.astral.sh/uv/getting-started/installation/",
            "Python con uv: docs.astral.sh/uv/guides/install-python/",
            "Git: git-scm.com/install/ | Git for Windows: gitforwindows.org/",
            "GitHub: docs.github.com/get-started/start-your-journey/creating-an-account-on-github",
            "Databricks Free Edition: docs.databricks.com/aws/en/getting-started/free-edition",
            "Editor recomendado: code.visualstudio.com/download",
            "curl: curl.se/download.html",
            "Postman: postman.com/downloads/ | Echo: postman-echo.com/get",
            "Docker y Compose: docs.docker.com/get-started/get-docker/ | docs.docker.com/compose/install/",
        ],
    ),
    assignment(
        1,
        2,
        "Ciclo observable de ML y AgentOps",
        "Runs comparables, gate, Registry, API local y evaluacion",
        "2 horas en clase + trabajo autonomo",
        "Parejas en Databricks Free Edition",
        "Assignment 1.1 completado y acceso a Databricks",
        (
            "Construir evidencia trazable de un ciclo de ML: comparar candidatos, "
            "aplicar un gate sin contaminar test, registrar el ganador, servirlo "
            "localmente y completar una traza y evaluacion determinista de agente."
        ),
        [
            "La clase 1 deja preparado el equipo y el workspace; la ficha de operacion se construye dentro de esta practica.",
            "El modo obligatorio de AgentOps/LLMOps es determinista; una llamada real a un endpoint es opcional y solo se hace si el docente lo indica.",
            "Cada run debe ser comparable: mismo split, nombres estables, tags de contexto y artefactos auditables.",
            "La API local es una practica de contrato y observabilidad; no es un despliegue publico ni sustituye Model Serving.",
        ],
        [
            "notebooks/01_tracking_mlops.ipynb",
            "notebooks/02_agent_llmops.ipynb con USE_LLM = False",
            "Databricks Experiments, Unity Catalog si esta disponible y el entorno verificado en S1.1",
            "exercise/01_tracking_mlops y exercise/02_agent_llmops como guias de detalle",
        ],
        [
            ("Configura el contexto", "Usa un alias de equipo no personal, el dataset de la practica y un experimento reconocible. No registres secretos, correos ni datos sensibles."),
            ("Genera candidatos", "Ejecuta seis candidatos con los mismos datos de particion. Registra parametros, metricas de entrenamiento/validacion, tags y artefactos auxiliares."),
            ("Aplica el gate", "Define una regla reproducible sobre validacion, descarta candidatos que no la cumplen y abre el test reservado solo para el ganador."),
            ("Registra y sirve", "Registra el modelo ganador, asigna el alias Champion si el entorno lo permite y prueba la API local con casos de exito y error. Apagala al terminar."),
            ("Traza y evalua", "Ejecuta el agente determinista, localiza route_question y retrieve_course_context, corre el scorer y explica por que no basta para autorizar produccion."),
        ],
        [
            ("Tabla de runs", "Seis runs con nombres, parametros, metricas, tags y artefactos."),
            ("Decision de modelo", "Regla del gate, ganador, test reservado, version y alias."),
            ("API local", "Resultados de checks validos e invalidos, identificador del run y apagado confirmado."),
            ("AgentOps/LLMOps", "Identificador de traza, scorer ejecutado y limite del criterio."),
            ("Ficha de operacion", "Experimento, gate, riesgos observados y evidencia nueva o pendiente."),
        ],
        [
            "Los runs contienen contexto suficiente para comparar y reproducir.",
            "El test aparece una sola vez para el ganador y no se usa para escogerlo.",
            "El modelo registrado conserva firma, version y alias cuando el entorno lo permite.",
            "La API muestra exito y errores sin dejar un proceso abierto.",
            "No aparecen secretos ni datos sensibles en runs, trazas o artefactos.",
        ],
        [("Tracking completo", "2"), ("Gate y test reservado", "2"), ("Registry/API", "2"), ("Trazas y evaluacion prudente", "2"), ("Evidencia y seguridad", "2")],
        [
            "Abrir la carpeta semana1 como Git Folder en Databricks.",
            "Ejecutar las celdas sin resolver y completar los TODO.",
            "Abrir Experiments y guardar capturas o enlaces de la tabla de runs.",
            "Entregar la ficha junto con identificadores de runs, traza y artefactos.",
        ],
        [
            "No compartas tokens personales ni copies credenciales al notebook.",
            "El alias Champion no equivale a aprobacion para produccion.",
            "Si Registry no esta disponible, documenta la limitacion y conserva la evidencia de tracking y API local.",
        ],
        [
            "semana1/modules/01-mlflow-databricks-foundations/exercises/01_tracking_mlops/README.md",
            "semana1/modules/01-mlflow-databricks-foundations/exercises/02_agent_llmops/README.md",
        ],
    ),
    assignment(
        2,
        1,
        "Del directorio vacio al proyecto reproducible",
        "Un proyecto pequeno para practicar entorno, dependencias y trazabilidad local",
        "45-50 min",
        "Parejas, terminal Bash",
        "uv y Git disponibles; no necesitas trabajo previo",
        (
            "Construir env-demo desde un directorio vacio y demostrar que una "
            "sola base de codigo se comporta de forma predecible en dev, pre y pro."
        ),
        [
            "Trabajad solo en local: esta practica no usa remoto ni parte del ejercicio de Wine.",
            "La pareja comparte pantalla y alterna quien escribe los comandos y quien contrasta la evidencia.",
            "El resultado debe usar un unico codigo, un unico uv.lock y un unico .venv para los tres entornos.",
        ],
        [
            "Una terminal Bash situada en un directorio de trabajo vacio",
            "uv y Git ya instalados",
            "Los dos cuadros de codigo incluidos en este documento",
        ],
        [
            (
                "Crea el proyecto",
                "Crea env-demo, entra en el directorio, ejecuta git init y despues uv init --package --vcs none .",
            ),
            (
                "Declara dependencias",
                "Crea .gitignore con .venv/, __pycache__/, .pytest_cache/ y .ruff_cache/. Anade Rich, Pytest y Ruff con los comandos indicados.",
            ),
            (
                "Revisa la estructura",
                "Localiza pyproject.toml, uv.lock, src/env_demo y tests. No crees carpetas distintas por entorno ni repitas dependencias.",
            ),
            (
                "Implementa el comando",
                "Sustituye src/env_demo/main.py por este codigo. La variable APP_ENV acepta dev, pre o pro, normaliza la entrada y Rich muestra el mensaje.",
            ),
            (
                "Prueba el contrato",
                "Crea tests/test_main.py con estos casos. El parametrizado cubre los tres valores admitidos y el ultimo protege el error.",
            ),
            (
                "Documenta y registra",
                "Escribe en README como instalar, ejecutar y comprobar. Haz tres commits locales, en orden, con las intenciones exactas indicadas abajo.",
            ),
        ],
        [
            ("Proyecto local", "pyproject.toml, uv.lock, paquete src, tests, README y .gitignore."),
            ("Historial", "Tres commits locales pequenos y legibles, sin configurar remoto."),
            ("Comprobacion", "Salida de los tres entornos, Pytest, Ruff y controles de Git."),
        ],
        [
            "Los tres entornos ejecutan exactamente el mismo paquete y cambian solo mediante APP_ENV.",
            "La entrada local provoca ValueError y los cuatro casos de prueba pasan.",
            "Rich es dependencia normal; Pytest y Ruff son dependencias de desarrollo.",
            ".venv no aparece entre los archivos versionados y uv.lock si aparece.",
            "README permite repetir el trabajo desde un checkout limpio.",
        ],
        [
            ("Proyecto y dependencias", "3"),
            ("Comando y entornos", "3"),
            ("Tests y calidad", "2"),
            ("README e historial", "2"),
        ],
        [
            "mkdir env-demo && cd env-demo\ngit init\nuv init --package --vcs none .\nprintf '.venv/\\n__pycache__/\\n.pytest_cache/\\n.ruff_cache/\\n' > .gitignore",
            "uv add rich\nuv add --dev pytest ruff",
            "APP_ENV=dev uv run python -m env_demo.main\nAPP_ENV=pre uv run python -m env_demo.main\nAPP_ENV=pro uv run python -m env_demo.main",
            "uv run pytest\nuv run ruff check .",
            "git log --oneline\ngit ls-files .venv",
        ],
        [
            "Commits, en orden: bootstrap uv project; add environment-aware command; add tests and usage documentation.",
            "Una sola base de codigo, uv.lock y .venv; no prepares variantes dev/pre/pro.",
            "Termina sin remoto: no publiques ni abras una revision.",
        ],
        [
            "Assignment autocontenido; configuracion en pyproject.toml",
        ],
        task_snippets={
            4: (
                "src/env_demo/main.py",
                '''import os

from rich import print

VALID_ENVIRONMENTS = {"dev", "pre", "pro"}


def environment_message(environment: str) -> str:
    normalized = environment.strip().lower()
    if normalized not in VALID_ENVIRONMENTS:
        raise ValueError("APP_ENV debe ser dev, pre o pro")
    return f"Entorno activo: {normalized.upper()}"


def main() -> None:
    print(environment_message(os.getenv("APP_ENV", "dev")))


if __name__ == "__main__":
    main()
''',
            ),
            5: (
                "tests/test_main.py",
                '''import pytest

from env_demo.main import environment_message


@pytest.mark.parametrize("environment", ["dev", "pre", "pro"])
def test_known_environment(environment: str) -> None:
    assert environment.upper() in environment_message(environment)


def test_unknown_environment() -> None:
    with pytest.raises(ValueError, match="APP_ENV"):
        environment_message("local")
''',
            ),
        },
    ),
    assignment(
        2,
        2,
        "De la practica de S1 a un proyecto revisable",
        "Ordenar el entrenamiento de Wine en un fork propio y abrir una revision segura",
        "120 min",
        "Parejas, fork propio",
        "Fork personal del curso y terminal Bash",
        (
            "Convertir los tres archivos de partida de S1 en un proyecto uv que "
            "otra pareja pueda instalar, ejecutar y revisar como pull request (PR)."
        ),
        [
            "Parte unicamente de semana2/starter/WineQT.csv, semana2/starter/train.py y semana2/starter/test_train.py.",
            "Todo el trabajo ocurre en vuestro fork. La rama de entrega es feature/s2-wine-project.",
            "La revision se abre contra main del mismo fork, nunca el repositorio docente.",
        ],
        [
            "Fork propio actualizado y clonado en local",
            "Los tres archivos de semana2/starter, sin reutilizar una solucion externa",
            "uv, Git, navegador y una terminal Bash",
        ],
        [
            (
                "Abre la rama",
                "Desde la raiz del fork ejecuta git switch -c feature/s2-wine-project y confirma que no estas trabajando sobre main.",
            ),
            (
                "Inicializa el paquete",
                "Ejecuta uv init --package --vcs none --name wine-quality semana2/wine-quality-project y entra en el nuevo proyecto.",
            ),
            (
                "Instala dependencias",
                "Anade pandas y scikit-learn como dependencias de ejecucion; anade Pytest y Ruff solo al grupo de desarrollo.",
            ),
            (
                "Migra el starter",
                "Copia WineQT.csv a data/raw/WineQT.csv, train.py a src/wine_quality/train.py y test_train.py a tests/test_train.py. Conserva esos destinos.",
            ),
            (
                "Cierra la reproducibilidad",
                "Ajusta rutas e imports, genera el lock y ejecuta uv sync --locked. El entrenamiento debe arrancar como modulo con el entorno bloqueado.",
            ),
            (
                "Documenta y revisa",
                "Explica en README instalacion, estructura y comprobaciones. Crea 2-3 commits, sube la rama y abre desde la web el pull request (PR).",
            ),
        ],
        [
            ("Proyecto uv", "Paquete, datos raw, tests, pyproject.toml, uv.lock y README."),
            ("Historial", "Rama con 2-3 commits que separan estructura, migracion y verificacion."),
            ("Revision", "Enlace a la revision abierta contra main del mismo fork."),
            ("Evidencia", "Salida del entrenamiento, Pytest y Ruff ejecutados con --frozen."),
        ],
        [
            "El proyecto nace del starter indicado y mantiene cada archivo en su destino acordado.",
            "El checkout se instala con uv sync --locked sin resolver versiones nuevas.",
            "El entrenamiento modular, los tests y Ruff terminan correctamente con --frozen.",
            "README explica el recorrido desde la raiz del fork.",
            "El pull request (PR) muestra 2-3 commits y tiene como base main del fork propio.",
        ],
        [
            ("Estructura y migracion", "3"),
            ("Entorno bloqueado", "2"),
            ("Ejecucion y tests", "3"),
            ("README y revision", "2"),
        ],
        [
            "git switch -c feature/s2-wine-project",
            "uv init --package --vcs none --name wine-quality semana2/wine-quality-project\ncd semana2/wine-quality-project",
            "uv add pandas scikit-learn\nuv add --dev pytest ruff",
            "mkdir -p data/raw tests\ncp ../starter/WineQT.csv data/raw/WineQT.csv\ncp ../starter/train.py src/wine_quality/train.py\ncp ../starter/test_train.py tests/test_train.py",
            "uv sync --locked",
            "uv run --frozen python -m wine_quality.train\nuv run --frozen pytest\nuv run --frozen ruff check .",
            "git push -u origin feature/s2-wine-project",
        ],
        [
            "Abre el pull request (PR) desde la web: origen feature/s2-wine-project y destino main del mismo fork.",
            "No anadas herramientas ni artefactos que no formen parte del objetivo: basta con el entrenamiento actual y su prueba.",
            "No cambies la base al repositorio docente. Si la web la selecciona, corrige el destino antes de crear la revision.",
        ],
        [
            "semana2/starter/WineQT.csv",
            "semana2/starter/train.py",
            "semana2/starter/test_train.py",
        ],
    ),
    assignment(
        3,
        1,
        "Lienzo de inferencia, contratos y preprocesado",
        "Especificar la frontera antes de escribir el modulo",
        "1 hora teoria + 1 hora demo guiada",
        "Parejas",
        "Entregable S2 y cinco muestras de vino",
        (
            "Definir el contrato que conecta una fila nueva con un modelo ya "
            "entrenado: campos, tipos, rangos, orden del vector, salida y fallos "
            "esperados."
        ),
        [
            "La semana 3 no entrena un modelo nuevo: el artefacto preentrenado lo distribuye el docente.",
            "El objetivo de esta practica es producir una especificacion ejecutable para la clase 2.",
            "sample_id identifica la solicitud pero no entra en el vector numerico del modelo.",
            "El orden de las once caracteristicas es parte del contrato, no un detalle de implementacion.",
        ],
        [
            "assets/03-wine-quality/inference_samples.csv",
            "exercises/01-local-inference/01.01-contract-and-preprocess-canvas/problem/",
            "notebook 01-inferencia-y-contratos-alumno.ipynb",
            "Esquema de salida con quality_band, confidence y versiones",
        ],
        [
            ("Clasifica las piezas", "Separa datos historicos de entrenamiento, artefacto entregado y datos nuevos de inferencia. Justifica que recibe cada frontera."),
            ("Construye la tabla de campos", "Para las once features indica nombre canonico, tipo, unidad, rango razonable y si admite valores ausentes."),
            ("Fija el orden", "Escribe el orden exacto del vector y demuestra por que cambiar dos columnas puede producir una prediccion silenciosamente incorrecta."),
            ("Diseña fallos", "Propone una fila valida, una columna desconocida, una fila fuera de rango y el momento del flujo en el que cada una debe fallar."),
            ("Define aceptacion", "Escribe tres criterios que el modulo de la clase 2 debera demostrar con tests y con un comando local."),
        ],
        [
            ("Tabla de contrato", "Once campos con nombres, tipos, unidades y limites."),
            ("Mapa de flujo", "CSV -> solicitud -> preprocesado -> vector -> artefacto -> prediccion."),
            ("Casos de fallo", "Dos entradas invalidas y etapa de rechazo esperada."),
            ("Criterios de aceptacion", "Tres reglas comprobables para el modulo local."),
        ],
        [
            "No se incluye sample_id en el vector del modelo.",
            "Los nombres y el orden de las once features coinciden con el artefacto de S3.",
            "La salida conserva categoria, confianza, version de modelo y version de preprocesado.",
            "Cada caso invalido tiene una razon y una etapa de fallo definida.",
            "Otra pareja puede implementar el modulo de la clase 2 usando solo el lienzo.",
        ],
        [("Contrato completo", "3"), ("Preprocesado y orden", "3"), ("Casos de fallo", "2"), ("Criterios ejecutables", "2")],
        [
            "Abrir el notebook o la hoja compartida de la practica.",
            "Completar el lienzo y discutirlo con otra pareja.",
            "Guardar una copia en el entregable del proyecto y anotar dudas para la clase 2.",
        ],
        [
            "No escribas todavia contracts.py ni inference.py.",
            "No añadas la etiqueta de calidad a las muestras de entrada.",
            "No confundas una confianza del modelo con una garantia del resultado.",
        ],
        [
            "semana3/modules/03-inference-contracts/exercises/01-local-inference/01.01-contract-and-preprocess-canvas/problem/readme.md",
            "semana3/modules/03-inference-contracts/guides/class-1-practices.md",
        ],
    ),
    assignment(
        3,
        2,
        "Modulo local de inferencia",
        "Convertir el lienzo en un comando reproducible",
        "2 horas",
        "Parejas, learning by doing",
        "Assignment 3.1 y starter con tests",
        (
            "Implementar un modulo local que lea un CSV, valide cada fila, "
            "preprocese en el orden entrenado, cargue el modelo ya entrenado y "
            "escriba predicciones sin dejar una salida parcial si falla una fila."
        ),
        [
            "Trabaja exclusivamente en problem/starter; la carpeta solutions es referencia del debrief.",
            "El `.joblib` ya contiene el estimador, feature_names y model_version; no hay que reentrenarlo.",
            "Las pruebas describen la interfaz publica: contratos, carga, inferencia y CLI.",
            "La implementacion debe dejar preparado el bundle que S4 empaquetara.",
        ],
        [
            "problem/starter/ con pyproject.toml, tests y TODOs",
            "models/wine_quality_classifier.joblib entregado por el docente",
            "assets/inference_samples.csv con cinco muestras",
            "Lienzo de contrato de la clase 1",
        ],
        [
            ("Lee la especificacion", "Ejecuta la suite roja y convierte cada nombre de test en una regla de la API local."),
            ("Implementa contratos", "Completa request y prediction con Pydantic; rechaza extras, tipos imposibles y valores fuera de rango."),
            ("Implementa preprocesado", "Construye un vector estable con las once features y una version explicita; no mezcles sample_id."),
            ("Implementa carga e inferencia", "Valida el payload del artefacto antes de invocar predict/predict_proba y valida la salida resultante."),
            ("Completa el CLI", "Lee todas las filas, acumula predicciones y escribe el CSV solo cuando el conjunto es valido."),
            ("Amplia los errores", "Prueba columna extra, segunda fila invalida y artefacto incompatible; confirma que no queda CSV parcial."),
        ],
        [
            ("Codigo del starter", "contracts.py, preprocess.py, inference.py y predict_file.py completados."),
            ("Tests", "Suite en verde, incluyendo casos de error y ausencia de salida parcial."),
            ("Comando", "CSV de cinco filas con sample_id, categoria, confianza y versiones."),
            ("Nota tecnica", "Responsabilidad de cada modulo y dos decisiones de diseño."),
        ],
        [
            "uv run pytest termina sin fallos.",
            "El cargador comprueba feature_names y la interfaz minima del estimador.",
            "El vector respeta el orden del entrenamiento y excluye sample_id.",
            "Una fila invalida no deja un fichero de salida parcial.",
            "El CSV de salida contiene sample_id, quality_band, confidence, model_version y preprocessing_version.",
        ],
        [("Contratos y validacion", "2"), ("Preprocesado e inferencia", "3"), ("CLI y atomicidad", "3"), ("Tests y explicacion", "2")],
        [
            "cd exercises/01-local-inference/01.02-wine-quality-inference-module/problem/starter",
            "uv sync",
            "uv run pytest",
            "uv run ruff check src tests",
            "uv run ruff format --check src tests",
            "uv run python -m model_inference.predict_file --input assets/inference_samples.csv --output .tmp/wine_predictions.csv",
        ],
        [
            "No leas CSV desde preprocess.py ni cargues joblib desde el CLI.",
            "No subas el artefacto binario al repositorio.",
            "Si el modelo real no esta disponible, usa los clasificadores pequeños de los tests para comprobar la interfaz.",
        ],
        [
            "semana3/modules/03-inference-contracts/exercises/01-local-inference/01.02-wine-quality-inference-module/problem/readme.md",
            "semana3/modules/03-inference-contracts/guides/class-2-workshop.md",
        ],
    ),
    assignment(
        4,
        1,
        "Contrato del artefacto y manifiesto",
        "Decidir que debe viajar con un modelo serializado",
        "1 hora teoria + 1 hora practica guiada",
        "Parejas",
        "Modulo local de S3 y payload joblib legado",
        (
            "Diseñar un bundle inspeccionable que separe el binario del estimador "
            "de los metadatos que permiten validar compatibilidad antes de inferir."
        ),
        [
            "Esta practica no implementa artifact.py: produce las decisiones que la clase 2 convertira en funciones y tests.",
            "El manifiesto debe poder leerlo una persona sin deserializar el estimador.",
            "La compatibilidad incluye schema, modelo, preprocesado, features, etiquetas e interfaz del estimador.",
            "joblib.load exitoso no significa artefacto compatible ni seguro por si solo.",
        ],
        [
            "notebook 01-artefacto-y-manifiesto-alumno.ipynb",
            "payload legado de S3 con estimator, feature_names y model_version",
            "exercises/01.01-artifact-contract/problem/readme.md",
            "Explainer con las seis claves del manifiesto",
        ],
        [
            ("Clasifica el contenido", "Asigna cada dato a model.joblib, manifest.json o codigo: estimador, versiones, nombres, etiquetas y reglas."),
            ("Completa el manifiesto", "Propone schema_version, model_version, preprocessing_version, feature_names, output_labels y estimator_type."),
            ("Escribe invariantes", "Define al menos tres condiciones que deben bloquear la carga o la inferencia antes de escribir resultados."),
            ("Rompe el contrato", "Altera orden de columnas, version de preprocesado, etiqueta de salida y tipo de estimador; predice el error y su etapa."),
            ("Decide la politica de filas", "Explica que debe pasar si la segunda fila de un CSV es invalida y por que no se debe publicar una salida parcial."),
        ],
        [
            ("Tabla de almacenamiento", "Que vive en binario, manifiesto y codigo, con justificacion."),
            ("Manifiesto propuesto", "JSON con las seis claves obligatorias y valores coherentes con S3."),
            ("Matriz de invariantes", "Cambio, comprobacion, error esperado y etapa de rechazo."),
            ("Politica de errores", "Decision sobre filas invalidas y salida atomica."),
        ],
        [
            "feature_names conserva exactamente los nombres y el orden de S3.",
            "preprocessing_version no se confunde con model_version.",
            "output_labels limita las categorias que puede exponer la respuesta.",
            "Se comprueba la interfaz predict/predict_proba del estimador.",
            "La politica de filas evita salidas parciales.",
        ],
        [("Separacion binario/metadatos", "2"), ("Manifiesto e invariantes", "4"), ("Casos invalidos", "2"), ("Decision de atomicidad", "2")],
        [
            "Abrir el notebook guiado o el notebook del alumnado.",
            "Completar el lienzo y contrastarlo con otra pareja.",
            "Guardar el manifiesto propuesto y la matriz de compatibilidad.",
        ],
        [
            "No implementes todavia save_model_bundle ni load_model_bundle.",
            "No presentes el manifiesto como una garantia de seguridad del binario.",
            "El clasificador pequeño del notebook es suficiente para probar la idea.",
        ],
        [
            "semana4/modules/04-model-packaging/exercises/01-model-packaging/01.01-artifact-contract/problem/readme.md",
            "semana4/modules/04-model-packaging/guides/class-1-practices.md",
        ],
    ),
    assignment(
        4,
        2,
        "Bundle serializado y CLI validado",
        "Guardar, cargar y consumir un modelo sin salida parcial",
        "2 horas",
        "Parejas, taller sobre starter",
        "Assignment 4.1 y contratos de S3",
        (
            "Implementar la nueva frontera de empaquetado: manifest.json, "
            "model.joblib, carga validada, inferencia validada y CLI que procesa "
            "todas las filas antes de publicar el resultado."
        ),
        [
            "Trabaja en problem/starter; contracts.py y preprocess.py de S3 ya estan preparados.",
            "Los tests usan un DummyClassifier para evitar descargas y binarios grandes.",
            "La carga debe validar metadatos antes de deserializar el objeto.",
            "El bundle sera la dependencia comun de la interfaz Streamlit de S5 y la API posterior.",
        ],
        [
            "problem/starter/ con TODOs en artifact.py y predict_file.py",
            "tests/ como especificacion ejecutable",
            "Lienzo de la clase 1",
            "CSV de muestras de semana 3 y bundle real opcional del docente",
        ],
        [
            ("Implementa el manifiesto", "Completa ArtifactManifest y create_manifest con campos estrictos, versiones, orden y etiquetas."),
            ("Implementa el guardado", "Escribe manifest.json y model.joblib de forma reproducible y valida la interfaz del estimador."),
            ("Implementa la carga", "Rechaza archivos ausentes, JSON incompatible y estimadores no compatibles antes de inferir."),
            ("Valida la salida", "Completa infer_wine_quality y exige etiqueta, confianza, modelo y preprocesado validos."),
            ("Completa el CLI", "Lee, valida e infiere todas las filas; abre la salida solo al final y conserva el esquema estable."),
            ("Añade un caso de fallo", "Incluye un manifest corrupto, una fila fuera de rango o una salida de modelo no permitida y prueba su mensaje."),
        ],
        [
            ("Bundle", "Directorio con manifest.json y model.joblib generado localmente."),
            ("Tests", "Suite en verde para guardado, carga, incompatibilidad, salida y CLI."),
            ("CSV de inferencia", "Salida con cinco predicciones y metadatos de version."),
            ("Nota de compatibilidad", "Dos ejemplos de cambios que deben bloquearse y por que."),
        ],
        [
            "El manifiesto no admite campos desconocidos ni versiones incompatibles.",
            "La carga valida el manifiesto antes de deserializar el estimador.",
            "La salida del modelo cumple el contrato de S3.",
            "Una fila posterior invalida no deja CSV publicado.",
            "El comando funciona sin depender del estado del notebook.",
        ],
        [("Manifiesto y guardado", "3"), ("Carga e inferencia", "3"), ("CLI y atomicidad", "2"), ("Tests y extension", "2")],
        [
            "cd exercises/01-model-packaging/01.02-serializable-inference-module/problem/starter",
            "uv sync",
            "uv run pytest",
            "uv run ruff check src tests",
            "uv run ruff format --check src tests",
            "uv run python -m model_packaging.predict_file --bundle models/wine_quality_bundle --input ../semana3/assets/03-wine-quality/inference_samples.csv --output .tmp/wine_predictions.csv",
        ],
        [
            "No dupliques el contrato ni el preprocesado de S3.",
            "No subas model.joblib al repositorio si la carpeta models esta ignorada.",
            "El bundle solo debe cargarse desde una fuente de confianza.",
        ],
        [
            "semana4/modules/04-model-packaging/exercises/01-model-packaging/01.02-serializable-inference-module/problem/readme.md",
            "semana4/modules/04-model-packaging/guides/class-2-workshop.md",
        ],
    ),
    assignment(
        5,
        1,
        "Del formulario a la inferencia: miniapp Churn",
        "Completar una miniapp guiada con una frontera de inferencia observable",
        "60 min",
        "Parejas, práctica guiada",
        "Starter de churn y teoría de formularios y reruns",
        (
            "Completar app.py sobre el predict() ya resuelto para recoger cuatro "
            "inputs, inferir solo al enviar y presentar un resultado comprensible."
        ),
        [
            "El starter aporta predict() completo: no se modifica la lógica del modelo.",
            (
                "Los cuatro inputs son tenure_months, monthly_spend_eur, "
                "support_calls y has_annual_contract."
            ),
            (
                "Un único st.form agrupa la edición; st.form_submit_button marca la "
                "frontera entre editar e inferir."
            ),
            (
                "Un ValueError se traduce a un mensaje seguro y accionable, sin "
                "traceback ni detalles internos."
            ),
        ],
        [
            "semana5/modules/05-streamlit-basic-model-ui/exercises/01-churn-streamlit/problem/starter/",
            "app.py con los TODO y src/churn_demo/model.py con predict() completo",
            "tests/ y fake de Streamlit para comprobar el rerun sin navegador",
        ],
        [
            (
                "Lee el contrato y anticipa dos predicciones · 0–10 min",
                (
                    "Lee la firma de predict() y anticipa el resultado para los "
                    "perfiles 2, 95, 4, False y 36, 35, 0, True."
                ),
            ),
            (
                "Construye el formulario · 10–25 min",
                (
                    "Crea los cuatro widgets dentro de un único st.form y añade "
                    "st.form_submit_button."
                ),
            ),
            (
                "Conecta submit y predict() · 25–35 min",
                (
                    "Mientras se edita debe haber cero llamadas; cada envío válido "
                    "hace una llamada a predict()."
                ),
            ),
            (
                "Presenta resultado y error · 35–45 min",
                (
                    "Muestra label, risk_score y explanation con etiquetas claras y "
                    "traduce ValueError a un mensaje seguro."
                ),
            ),
            (
                "Ejecuta los tests · 45–55 min",
                (
                    "Corrige cada contrato incumplido hasta dejar las 13 pruebas "
                    "verdes y el formato limpio."
                ),
            ),
            (
                "Cierra QA y puente · 55–60 min",
                (
                    "Registra los cuatro casos manuales y explica qué patrón se "
                    "conservará al pasar al contrato Wine."
                ),
            ),
        ],
        [
            (
                "Código",
                "app.py completo; predict() permanece como lo entrega el starter.",
            ),
            (
                "Pruebas",
                "Salida de la suite con las 13 pruebas verdes y formato limpio.",
            ),
            (
                "QA manual",
                "Registro breve de los cuatro casos y su resultado observable.",
            ),
        ],
        [
            "Aparecen exactamente los cuatro inputs dentro de un único st.form.",
            "Editar provoca cero llamadas y st.form_submit_button provoca una llamada.",
            "label, risk_score y explanation se muestran tras un envío válido.",
            "ValueError produce un error seguro, accionable y sin detalle interno.",
            "Las 13 pruebas y los cuatro casos de QA quedan verdes.",
        ],
        [
            ("Formulario y widgets", "2"),
            ("Submit 0/1", "2"),
            ("Separación UI/inferencia", "2"),
            ("Resultado y error", "2"),
            ("Tests y QA", "2"),
        ],
        [
            "cd semana5/modules/05-streamlit-basic-model-ui/exercises/01-churn-streamlit/problem/starter",
            "uv sync",
            "uv run python -m pytest -q",
            "uv run ruff check app.py src tests",
            "uv run ruff format --check app.py src tests",
            "uv run streamlit run app.py",
        ],
        [
            "No añadas session_state, caché, entrenamiento ni persistencia.",
            (
                "El patrón formulario-submit-inferencia será el puente conceptual a "
                "la segunda práctica."
            ),
        ],
        [
            "semana5/modules/05-streamlit-basic-model-ui/exercises/01-churn-streamlit/README.md",
            "semana5/modules/05-streamlit-basic-model-ui/exercises/01-churn-streamlit/problem/starter/README.md",
        ],
    ),
    assignment(
        5,
        2,
        "Del bundle S4 al frontal Wine",
        "Implementar el formulario y la salida sobre el bundle real de S4",
        "120 min",
        "Parejas, taller guiado sobre starter",
        "Bundle Wine de S4 válido y starter de la práctica",
        (
            "Completar collect_values() y render_prediction() para conectar los "
            "once campos preparados con el gateway y el bundle real de S4."
        ),
        [
            (
                "El runtime exige MODEL_UI_BUNDLE apuntando a un directorio real con "
                "manifest.json y model.joblib; no existe alternativa de ejecución."
            ),
            (
                "El starter ya incluye completos los once campos de FIELD_SPECS; no "
                "se rediseña el esquema."
            ),
            (
                "Un único st.form y st.form_submit_button garantizan cero llamadas al "
                "editar y una llamada al enviar."
            ),
            (
                "La única frontera permitida es gateway.predict(values); los dobles "
                "se usan exclusivamente dentro de tests/."
            ),
        ],
        [
            "semana5/modules/05-streamlit-basic-model-ui/exercises/02-first-streamlit/problem/starter/",
            "Bundle real de S4 con manifest.json y model.joblib",
            "FIELD_SPECS completo, gateway de bundle y fakes confinados a tests/",
        ],
        [
            (
                "Localiza y valida el bundle · 0–15 min",
                (
                    "Define MODEL_UI_BUNDLE y verifica que el directorio real contiene "
                    "manifest.json y model.joblib."
                ),
            ),
            (
                "Construye los widgets · 15–35 min",
                (
                    "Implementa collect_values() generando los once widgets desde "
                    "FIELD_SPECS, sin cambiar nombres, orden ni límites."
                ),
            ),
            (
                "Completa formulario y submit · 35–55 min",
                (
                    "Agrupa los widgets en un st.form y devuelve el estado de "
                    "st.form_submit_button junto con values."
                ),
            ),
            (
                "Revisa la frontera gateway · 55–75 min",
                (
                    "Comprueba cero llamadas al editar y una al enviar, exclusivamente "
                    "mediante gateway.predict(values)."
                ),
            ),
            (
                "Presenta el resultado · 75–90 min",
                (
                    "Implementa render_prediction() con quality_band, confidence, "
                    "model_version y "
                    "preprocessing_version con copy honesto."
                ),
            ),
            (
                "Prueba bundle ausente · 90–105 min",
                (
                    "Comprueba la frontera segura ante bundle ausente o inválido, sin "
                    "rutas, traceback ni detalle interno."
                ),
            ),
            (
                "Ejecuta tests y QA · 105–115 min",
                (
                    "Deja 27 pruebas verdes y registra los cuatro casos con bundle "
                    "real, edición, submit y bundle ausente."
                ),
            ),
            (
                "Documenta ejecución y límites · 115–120 min",
                (
                    "Documenta el comando de arranque, la configuración del bundle y "
                    "los límites que se abordarán en S6."
                ),
            ),
        ],
        [
            (
                "Código",
                "app.py con collect_values() y render_prediction() completas.",
            ),
            (
                "Configuración del bundle",
                (
                    "Comando de MODEL_UI_BUNDLE y ruta esperada documentados sin "
                    "publicar el binario."
                ),
            ),
            (
                "Evidencias",
                "Capturas o registro equivalente con bundle real y bundle ausente.",
            ),
            (
                "Pruebas y QA",
                "Salida de las 27 pruebas verdes y matriz de cuatro casos.",
            ),
        ],
        [
            "Con MODEL_UI_BUNDLE válido aparecen los once widgets de FIELD_SPECS.",
            "Editar causa cero llamadas; un submit causa una llamada a gateway.predict(values).",
            "La pantalla muestra quality_band, confidence, model_version y preprocessing_version.",
            "Bundle ausente o inválido e inferencia inválida producen errores seguros.",
            "Las 27 pruebas y los cuatro casos de QA quedan verdes.",
        ],
        [
            ("Bundle real y contrato Wine", "2"),
            ("Formulario y submit", "2"),
            ("Frontera gateway", "2"),
            ("Resultado y error", "2"),
            ("Reproducibilidad, tests y QA", "2"),
        ],
        [
            "cd semana5/modules/05-streamlit-basic-model-ui/exercises/02-first-streamlit/problem/starter",
            "uv sync",
            "$env:MODEL_UI_BUNDLE = 'RUTA_AL_BUNDLE_DE_S4'",
            "uv run python -m pytest -q",
            "uv run ruff check app.py src tests",
            "uv run ruff format --check app.py src tests",
            "uv run --with 'streamlit>=1.40,<2.0' streamlit run app.py",
        ],
        [
            (
                "Sin joblib ni preprocesado en app.py; state, caché, telemetría y "
                "persistencia quedan para S6."
            ),
        ],
        [
            "semana5/modules/05-streamlit-basic-model-ui/exercises/02-first-streamlit/README.md",
        ],
    ),
    assignment(
        6,
        1,
        "Mapa de estado de la app de S5",
        "Diseñar reruns, cache, estados y recuperacion",
        "1 hora teoria + 1 hora demo guiada",
        "Parejas",
        "App funcional de S5",
        (
            "Inspeccionar la app de S5 y especificar que debe persistir, que debe "
            "cachearse, que eventos producen cada transicion y que debe ver la "
            "persona durante una inferencia."
        ),
        [
            "S6 no rediseña el formulario: conserva el contrato Wine, collect_values y el gateway de S5.",
            "Una variable local puede desaparecer al rerun; session_state conserva estado de sesion, no sustituye un almacen de datos.",
            "cache_resource es para el gateway o bundle reutilizable, no para respuestas personales.",
            "Una respuesta valida pero lenta sigue siendo success con una señal tecnica.",
        ],
        [
            "App de S5 entregada por la pareja o solucion base",
            "exercises/01-ui-contract/problem/01-estado-streamlit-alumno.ipynb",
            "Contrato y manifest de S4",
            "Demo guiada de estados de S6",
        ],
        [
            ("Inspecciona S5", "Localiza formulario, gateway, llamada predict y puntos donde un rerun puede perder el resultado."),
            ("Diseña session_state", "Decide claves minimas para last_state, telemetry y valores de retry; justifica que no guardaras en telemetria."),
            ("Diseña la cache", "Indica que funcion se envuelve con st.cache_resource y por que no debe cachearse el payload de una persona."),
            ("Define transiciones", "Completa idle -> loading -> success/error con evento, mensaje, accion permitida y evidencia."),
            ("Diseña recuperacion", "Incluye entrada invalida, bundle ausente, fallo transitorio, retry y clear sin borrar telemetria."),
        ],
        [
            ("Contrato de sesion", "Claves, tipos, ciclo de vida y politica de limpieza."),
            ("Maquina de estados", "Tabla de estados, eventos, mensajes, acciones y evidencia."),
            ("Decision de cache", "Recurso cacheable, argumento de cache y dato excluido."),
            ("Plan de implementacion", "Relacion entre requisitos, funciones y tests de la practica 6.2."),
        ],
        [
            "El diseño parte de una limitacion observable de S5.",
            "Distingue estado de sesion, recurso cacheado y datos de una peticion.",
            "Las transiciones tienen eventos y acciones observables.",
            "La confianza no se presenta como certeza ni la latencia como error de modelo.",
            "Otra pareja puede implementar el taller sin inventar estados.",
        ],
        [("Lectura de S5", "2"), ("Estado y cache", "3"), ("Transiciones y recuperacion", "3"), ("Plan implementable", "2")],
        [
            "Abrir la app de S5 y el notebook de diseño.",
            "Completar tablas de estado, cache y transiciones.",
            "Contrastar el plan con los tests del starter de la practica 6.2.",
        ],
        [
            "No copies el formulario para crear una segunda app.",
            "No guardes los valores completos de entrada en Telemetry.",
            "Los umbrales de confianza y latencia son politicas de UX de la demo, no calibracion del modelo.",
        ],
        [
            "semana6/modules/06-ux-model-consumption/exercises/01-ui-contract/problem/README.md",
            "semana6/modules/06-ux-model-consumption/guides/class-1-practices.md",
        ],
    ),
    assignment(
        6,
        2,
        "Evolucion robusta de la interfaz de S5",
        "Estado explicito, gateway cacheado y UX operable",
        "2 horas",
        "Parejas, refactor sobre snapshot",
        "Assignment 6.1 y app de S5",
        (
            "Refactorizar la app de S5 para soportar reruns de forma explicita, "
            "conservar el ultimo resultado, comunicar loading/success/error, "
            "reintentar fallos y registrar telemetria agregada sin payloads."
        ),
        [
            "El starter es un snapshot de S5: el formulario y el gateway ya estan hechos.",
            "Los TODO nuevos estan en session.py, policies.py, presentation.py, controller.py y app.py.",
            "PredictionController no importa Streamlit; en S7 la misma frontera podra consumir HTTP.",
            "El resultado lento sigue siendo valido: above_target es una señal, no un error de contrato.",
        ],
        [
            "exercises/02-robust-streamlit/problem/starter/",
            "Tests de controller, presentation, gateway, session y telemetry",
            "Snapshot de S5 con sus once campos",
            "DemoGateway, UnavailableGateway y politicas proporcionadas",
        ],
        [
            ("Completa la sesion", "Inicializa de forma idempotente last_state, telemetry y last_values; clear vuelve a idle sin borrar contadores."),
            ("Implementa politicas", "Clasifica confianza low/medium/high y latencia within_target/above_target con limites explicitos."),
            ("Construye la vista", "Traduce PredictionPayload a un view model con copy seguro, versiones y mensaje de latencia."),
            ("Implementa el controlador", "Emite loading, mide latencia, valida la salida, traduce excepciones, crea request_id y registra agregados."),
            ("Cablea Streamlit", "Usa cache_resource para el gateway, session_state para estado observable, placeholder/status para loading y botones de retry/clear."),
            ("Prueba cuatro recorridos", "Exito, error de contrato, bundle ausente y respuesta lenta; verifica que no se muestran traceback ni features en telemetry."),
        ],
        [
            ("Diff de evolucion", "Identifica que se conserva de S5 y que se añade en S6."),
            ("App avanzada", "Resultado persistente, cache, loading, error, retry y clear funcionales."),
            ("Tests", "Suite verde y casos de confianza/latencia comprobados."),
            ("Telemetria", "Snapshot con contadores, errores, latencias y versiones, sin payload."),
            ("Evidencia visual", "Capturas o registro de exito, fallo, retry y limpieza."),
        ],
        [
            "La app mantiene el formulario y el contrato de S5.",
            "El gateway se carga como recurso y no por cada rerun.",
            "Se observan idle, loading, success y error.",
            "Retry y clear funcionan; clear conserva telemetria.",
            "Confianza y latencia se comunican sin sobreafirmar.",
            "Los errores tienen recuperacion y request_id, sin traceback ni payload.",
        ],
        [("Sesion y cache", "2"), ("Politicas y view model", "2"), ("Controlador", "3"), ("App y UX", "2"), ("Evidencia", "1")],
        [
            "cd modules/06-ux-model-consumption/exercises/02-robust-streamlit/problem/starter",
            "uv sync",
            "uv run pytest",
            "uv run ruff check src tests",
            "uv run ruff format --check src tests",
            "uv run --with 'streamlit>=1.40,<2.0' streamlit run app.py",
        ],
        [
            "No reimplementes collect_values ni el contrato de S4.",
            "No uses cache_resource como cache global de respuestas por usuario.",
            "La solucion docente se consulta en el debrief, no para copiar TODOs.",
        ],
        [
            "semana6/modules/06-ux-model-consumption/exercises/02-robust-streamlit/README.md",
            "semana6/modules/06-ux-model-consumption/guides/class-2-workshop.md",
        ],
    ),
    assignment(
        7,
        1,
        "De curl a un cliente Python",
        "Consumir una API de predicción como caja negra",
        "75-90 min",
        "Parejas, assignment posterior a la clase 1",
        "Microejercicios HTTP/JSON y API local preparada",
        (
            "Observar el contrato de una API de predicción y completar un cliente "
            "Python que trate de forma explícita petición, status, transporte y JSON."
        ),
        [
            "La API de bombas se entrega como caja negra: se ejecuta, pero no se modifica.",
            "El recorrido comienza con curl y termina con cinco pruebas del cliente en verde.",
            "Postman es una ampliación opcional y no forma parte de la calificación.",
        ],
        [
            "exercises/02-api-client-lab/problem/starter/client.py con los marcadores 3-6",
            "Cinco pruebas con sesiones y respuestas controladas",
            "API local y muestras JSON válidas e inválidas",
            "Guía curl con variantes Bash y PowerShell",
        ],
        [
            (
                "Prepara dos terminales",
                "Desde la raíz del módulo sincroniza el entorno, arranca la API en la primera terminal y conserva la segunda para observación y tests.",
            ),
            (
                "Observa el contrato",
                "Comprueba GET /health, un POST válido y un POST inválido; registra 200, 200 y 422, request_id y campo rechazado.",
            ),
            (
                "Ejecuta el estado inicial",
                "Lanza la suite del starter y confirma cinco pruebas rojas por el NotImplementedError intencional.",
            ),
            (
                "Implementa la petición",
                "Usa POST /v1/predictions, json=payload, Accept application/json y timeout explícito sin cambiar la firma pública.",
            ),
            (
                "Traduce fallos y valida",
                "Aplica raise_for_status; traduce HTTP, timeout y ConnectionError a PredictionClientError; decodifica JSON y exige un objeto.",
            ),
            (
                "Verifica y reúne evidencia",
                "Obtén cinco pruebas verdes y conserva las tres respuestas curl y una explicación sobre el reintento de POST.",
            ),
        ],
        [
            ("Cliente", "starter/client.py completado sin modificar la API de caja negra."),
            ("Tests", "Salida final con cinco pruebas verdes."),
            (
                "Evidencia HTTP",
                "Salud, POST 200 y POST 422 con status, request_id y campo rechazado.",
            ),
            (
                "Decisión",
                "Una frase que justifique por qué no se reintenta un POST ciegamente.",
            ),
        ],
        [
            "La petición usa la ruta, cuerpo JSON, cabecera Accept y timeout indicados.",
            "raise_for_status impide interpretar un 422 como una predicción correcta.",
            "HTTPError conserva el status; timeout y ConnectionError se distinguen.",
            "Una respuesta 2xx solo se acepta si contiene un objeto JSON.",
            "Las cinco pruebas pasan y la evidencia contiene 200, 200 y 422.",
            "No se modifica el servidor ni se copia la solución docente.",
        ],
        [
            ("Petición HTTP", "3"),
            ("Tratamiento de errores", "2"),
            ("Validación de respuesta", "2"),
            ("Tests y evidencias", "2"),
            ("Explicación y reproducibilidad", "1"),
        ],
        [
            "# Terminal 1 - servidor\ncd semana7/modules/07-http-rest-clients\nuv sync\nuv run python examples/pump-maintenance-api/server.py",
            (
                "# Terminal 2 - Bash o Git Bash\n"
                "cd semana7/modules/07-http-rest-clients\n"
                "BASE_URL=http://127.0.0.1:8000\n"
                "curl -i \"$BASE_URL/health\"\n"
                "curl -i -X POST \"$BASE_URL/v1/predictions\" \\\n"
                "  -H \"Accept: application/json\" \\\n"
                "  -H \"Content-Type: application/json\" \\\n"
                "  --data-binary @examples/pump-maintenance-api/samples/prediction-valid.json\n"
                "# Repite con prediction-invalid.json"
            ),
            (
                "# Terminal 2 - tests\n"
                "uv run python -m unittest discover "
                "-s exercises/02-api-client-lab/problem/starter -p \"test_*.py\" -v"
            ),
        ],
        [
            "No abras ni modifiques el servidor; en S7 se observa como caja negra.",
            "No implementes FastAPI ni autenticación: el backend comienza en S8.",
            "No uses Wine, Streamlit ni HttpInferenceGateway; pertenecen a la Clase 2.",
            "PowerShell: usa curl.exe y los comandos equivalentes de examples/curl/README.md.",
        ],
        [
            "semana7/modules/07-http-rest-clients/exercises/02-api-client-lab/problem/README.md",
            "semana7/modules/07-http-rest-clients/guides/class-1-practices.md",
            "semana7/modules/07-http-rest-clients/examples/curl/README.md",
        ],
    ),
    assignment(
        7,
        2,
        "De gateway local a cliente HTTP",
        "Consumir la API Wine sin alterar la experiencia construida en S6",
        "120 min",
        "Parejas, taller sobre starter",
        "Assignment 6.2 y app robusta de S6",
        (
            "Implementar HttpInferenceGateway para que la app robusta de S6 "
            "consuma la API Wine local por HTTP, manteniendo su interfaz y su "
            "comportamiento observable."
        ),
        [
            "Conserva la UI, PredictionController, estado de sesion, presentacion y telemetria de S6; sustituye solo el gateway local.",
            "La API Wine local se entrega como caja negra: observa su contrato, pero no abras ni modifiques el servidor.",
            "El contrato de red usa POST /v1/predictions y un cuerpo JSON con la forma {\"features\": ...}.",
            "En esta semana implementas el cliente; el servidor de S8 queda como siguiente frontera del proyecto.",
        ],
        [
            "exercises/03-wine-http-gateway/problem/starter/ con la app de S6 y TODOs del cliente",
            "Tests con sesiones y respuestas controladas como especificacion ejecutable",
            "API Wine local preparada como caja negra docente",
            "PredictionPayload y errores de dominio heredados de S6",
        ],
        [
            (
                "Mapea el contrato",
                "Identifica URL, metodo, cabecera Accept, cuerpo, respuesta valida y significado de 422 y 503 antes de completar codigo.",
            ),
            (
                "Implementa la peticion",
                "Completa HttpInferenceGateway con POST /v1/predictions, json={\"features\": values}, Accept application/json y un timeout explicito.",
            ),
            (
                "Valida la respuesta",
                "Decodifica el JSON de exito y validalo con PredictionPayload; rechaza JSON mal formado o un payload incompatible.",
            ),
            (
                "Traduce los fallos",
                "Convierte 422, 503, timeout y error de conexion en errores de dominio que el controlador de S6 ya sabe presentar.",
            ),
            (
                "Cablea la app",
                "Lee MODEL_API_URL, crea el gateway como recurso reutilizable e inyectalo en el mismo controlador sin duplicar estado ni telemetria.",
            ),
            (
                "Reune evidencia",
                "Ejecuta tests y Ruff; arranca la API caja negra y la app, y registra un exito y un fallo recuperable sin mostrar trazas ni features.",
            ),
        ],
        [
            ("Cliente HTTP", "HttpInferenceGateway y sus tests de contrato, salida y transporte."),
            ("Wiring", "Diff pequeno que conserva UI, controlador, estado y telemetria de S6."),
            ("Comprobaciones", "Salida de Pytest y Ruff desde la raiz del modulo."),
            ("Recorrido", "Evidencia de la app conectada a la API local y de un fallo traducido."),
        ],
        [
            "La app conserva el formulario, PredictionController, estados, retry, clear y telemetria agregada de S6.",
            "La peticion usa POST /v1/predictions, json={\"features\": ...}, Accept application/json y timeout explicito.",
            "Toda respuesta 2xx se valida con PredictionPayload antes de llegar al controlador.",
            "422, 503, timeout y conexion se traducen sin filtrar traceback, cuerpo interno ni features.",
            "MODEL_API_URL configura el destino y la app funciona contra la API Wine local preparada.",
            "Los tests del cliente no dependen de un servidor real y la evidencia incluye la comprobacion integrada.",
        ],
        [
            ("Contrato y peticion", "2"),
            ("Validacion de respuesta", "2"),
            ("Errores y resiliencia", "2"),
            ("Wiring y continuidad", "2"),
            ("Tests y evidencia", "2"),
        ],
        [
            "# Terminal 1 - servidor\ncd semana7/modules/07-http-rest-clients\nuv sync\nuv run python examples/wine-quality-api/server.py",
            "# Terminal 2 - app\ncd semana7/modules/07-http-rest-clients/exercises/03-wine-http-gateway/problem/starter\nuv sync --extra app\nuv run pytest -q\nuv run ruff check src tests app.py\nuv run ruff format --check src tests app.py",
            "# Bash\nMODEL_API_URL=http://127.0.0.1:8000 uv run streamlit run app.py",
            "# PowerShell\n$env:MODEL_API_URL=\"http://127.0.0.1:8000\"; uv run streamlit run app.py",
        ],
        [
            "No implementes un backend: la API Wine es una caja negra y el servidor de S8 queda fuera de alcance.",
            "No anadas autenticacion ni secretos; esta practica solo configura una URL local.",
            "No registres valores de features ni cuerpos de respuesta en la telemetria.",
            "No cambies el contrato de PredictionPayload para adaptar una respuesta incorrecta.",
        ],
        [
            "semana7/modules/07-http-rest-clients/exercises/03-wine-http-gateway/problem/starter/README.md",
            "semana7/modules/07-http-rest-clients/guides/class-2-workshop.md",
        ],
    ),
    assignment(
        9,
        1,
        "Lo que le falta a una API que ya responde",
        "Microejercicios de serialización, errores, OpenAPI y tests sobre las demos",
        "4 x 5 min en la clase de 2 h",
        "Individual, durante la clase 1",
        "API funcional de S8; Python 3.12+ y uv",
        (
            "Observar en demos FastAPI ejecutables los cuatro huecos de una API que "
            "ya responde: salida sin contrato, errores con formas distintas, "
            "documentación que no refleja la API y ningún test que avise si el "
            "contrato cambia."
        ),
        [
            "No se escribe una API nueva: se ejecutan, observan y modifican temporalmente las demos de examples/; la Wine Quality API de S8 no se toca hasta la clase 2.",
            "Cada microejercicio cierra un bloque de teoría: M1 serialización, M2 errores, M3 OpenAPI y M4 tests.",
            "Las demos son deterministas y docentes: ningún score representa una decisión real de crédito ni de calidad.",
            "Lo que observes hoy es el requisito previo directo del workshop de la clase 2.",
        ],
        [
            "examples/serialization_demo.py, errors_demo.py y openapi_demo.py: una app FastAPI de un archivo por bloque",
            "tests/test_examples.py con TestClient, parametrize y dependency_overrides",
            "exercises/01-api-microexercises/problem/README.md con las preguntas de M1-M4",
            "Entorno del módulo con uv.lock; /docs, /redoc y /openapi.json en http://127.0.0.1:8000",
        ],
        [
            (
                "Prepara el entorno",
                "Desde semana9/modules/09-api-professional sincroniza con uv sync --locked y confirma con uv run pytest -q que las demos parten con 9 tests en verde.",
            ),
            (
                "M1 - Serialización",
                "Con serialization_demo.py compara /v1/scores/leaky y /v1/scores/public; anota los campos que solo aparecen en la primera, explica por qué /v1/scores/filtered tampoco los devuelve aunque la función retorna un dict y mira en /docs si PublicScore incluye is_reliable.",
            ),
            (
                "M2 - Errores",
                "Con errors_demo.py envía a POST /v1/scores los tres cuerpos del enunciado y llama a GET /v1/nada y GET /v1/boom; tabula status, error.code y error.fields. Comenta el decorador de handle_validation, observa la respuesta por defecto y restáuralo.",
            ),
            (
                "M3 - OpenAPI",
                "Con openapi_demo.py localiza en /openapi.json dónde terminan summary, docstring y responses de create_score; ejecuta el ejemplo minor con Try it out y añade un tercer ejemplo no_income sin el campo income.",
            ),
            (
                "M4 - Tests",
                "En tests/test_examples.py localiza el test con dependency_overrides, quita temporalmente raise_server_exceptions=False del fixture errors_client y explica qué cambia; escribe un test para income: 0.",
            ),
            (
                "Restaura y verifica",
                "Deshaz los cambios temporales de M2 y M4; si conservas el ejemplo de M3, adapta el test que cuenta ejemplos. Deja pytest y Ruff en verde con tu test incluido.",
            ),
        ],
        [
            ("M1", "Campos filtrados y una frase sobre qué hace response_model con lo que no declara."),
            ("M2", "Tabla de las cinco respuestas de error y respuesta por defecto sin el manejador."),
            ("M3", "Ubicación en /openapi.json y desplegable de Swagger con tres ejemplos."),
            ("M4", "Explicación del cambio en el fixture y salida de pytest con tu test en verde."),
        ],
        [
            "La respuesta de M1 menciona response_model y qué hace con los campos que no declara.",
            "Las cinco respuestas de error de M2 tienen la clave error en la raíz y ninguna contiene TU_SECRETO.",
            "handle_validation queda restaurado tras observar el {\"detail\": ...} por defecto de FastAPI.",
            "Swagger muestra tres ejemplos y la suite sigue en verde, o el cambio de M3 se deshace.",
            "El test nuevo de M4 comprueba 422 y fields[0].field == \"income\" para income: 0.",
            "uv run pytest -q y uv run ruff check . terminan en verde desde la raíz del módulo.",
        ],
        [
            ("M1 - Serialización y filtrado", "2"),
            ("M2 - Sobre de error y fallos seguros", "3"),
            ("M3 - OpenAPI fiel a la API", "2"),
            ("M4 - Test nuevo y overrides", "2"),
            ("Restauración y reproducibilidad", "1"),
        ],
        [
            (
                "# Terminal 1 - demos\n"
                "cd semana9/modules/09-api-professional\n"
                "uv sync --locked\n"
                "uv run fastapi dev examples/serialization_demo.py\n"
                "# M2: examples/errors_demo.py   M3: examples/openapi_demo.py"
            ),
            (
                "# Terminal 2 - M2 con curl (Bash o Git Bash)\n"
                "BASE_URL=http://127.0.0.1:8000\n"
                "curl -i -X POST \"$BASE_URL/v1/scores\" \\\n"
                "  -H \"Content-Type: application/json\" \\\n"
                "  -d '{\"age\": \"treinta\", \"income\": 1000}'\n"
                "curl -i \"$BASE_URL/v1/nada\"\n"
                "curl -i \"$BASE_URL/v1/boom\""
            ),
            (
                "# Terminal 2 - M4 y comprobación final\n"
                "cd semana9/modules/09-api-professional\n"
                "uv run pytest -q\n"
                "uv run ruff check ."
            ),
        ],
        [
            "No escribas una API nueva ni toques la Wine Quality API: es el trabajo de la clase 2.",
            "Cambia de demo con Ctrl+C; las tres escuchan en el puerto 8000.",
            "PowerShell: usa curl.exe o lanza las peticiones desde /docs.",
            "La solución comentada se comparte al final de la clase.",
        ],
        [
            "semana9/modules/09-api-professional/exercises/01-api-microexercises/problem/README.md",
            "semana9/modules/09-api-professional/examples/README.md",
            "semana9/modules/09-api-professional/sessions/01-teoria-api-profesional/README.md",
        ],
    ),
    assignment(
        9,
        2,
        "Wine Quality API v1.1",
        "Hacer cumplir, documentar y probar el contrato de S7 sin romper a sus clientes",
        "120 min",
        "Individual, taller guiado por tests",
        "Assignment 9.1 y API funcional de S8",
        (
            "Llevar la Wine Quality API de 1.0.0 a 1.1.0 completando los TODO del "
            "starter en orden: salida tipada y filtrada, errores con un único sobre, "
            "OpenAPI útil para quien consume y tests propios que demuestren el contrato."
        ),
        [
            "El contrato público de S7 no cambia: POST /v1/predictions, GET /health y el sobre de error con code, message, fields y request_id se hacen cumplir y se documentan, no se rediseñan.",
            "El starter es la API de S8: valida la entrada con Pydantic y carga el predictor una vez en el lifespan, pero devuelve dicts y errores {\"detail\": ...}.",
            "Al empezar, uv run pytest -q da 4 tests en verde y 23 en rojo; cada test en rojo corresponde a un TODO S9.",
            "Checkpoints: 8 en verde tras S9.1, 16 tras S9.2, 23 tras S9.3 y la suite completa tras S9.4.",
        ],
        [
            "exercises/02-wine-api-hardening/problem/starter/ con su propio uv.lock y los TODO S9.1-S9.4",
            "Suite de aceptación de S9.1-S9.3 como especificación ejecutable",
            "predictor.py, request_id.py y dependencies.py terminados; export_openapi.py para el snapshot",
            "WINE_API_MODE=unavailable para simular un modelo no cargado",
        ],
        [
            (
                "Arranca y mapea",
                "Sincroniza el starter, confirma 23 tests en rojo y 4 en verde y localiza los TODO con grep -rn \"TODO S9\" src tests antes de editar.",
            ),
            (
                "S9.1 - Contrato de salida",
                "Declara en Prediction solo los cuatro campos públicos del contrato; decide en el contrato, no en el predictor, cómo se redondea confidence y cómo se escribe served_at en UTC con sufijo Z. Las rutas devuelven modelos tipados.",
            ),
            (
                "S9.2 - Errores",
                "Implementa y registra los manejadores de validación, WineApiError, HTTPException de Starlette y error inesperado; /health lanza ModelUnavailableError. Cada fallo recibe su status y error.code sin filtrar detalles internos.",
            ),
            (
                "S9.3 - OpenAPI",
                "Completa los metadatos de la app, versión incluida; prefix, tags y responses 400, 422 y 503 en el APIRouter; description con unidad en cada Field; summary, docstring y al menos tres ejemplos de cuerpo en Swagger.",
            ),
            (
                "S9.4 - Tests propios",
                "Sustituye los cuatro pytest.fail: 503 con dependency_overrides y limpieza, cinco o más casos fuera de contrato con parametrize, límites inclusivos de alcohol y snapshot de OpenAPI.",
            ),
            (
                "Versiona y reúne evidencia",
                "Exporta y versiona contracts/openapi.json, deja pytest y Ruff en verde, captura /docs y redacta la nota de compatibilidad.",
            ),
        ],
        [
            ("API 1.1.0", "TODO resueltos y uv run pytest -q sin fallos."),
            ("contracts/openapi.json", "Snapshot generado con wine_api.export_openapi y versionado en Git."),
            ("Calidad", "uv run ruff check . y uv run ruff format --check . en verde."),
            ("Captura de /docs", "Predicción desplegada con errores 400, 422 y 503 y ejemplos de cuerpo."),
            ("Nota de compatibilidad", "5-10 líneas: qué cambio es compatible, cuál rompería a los clientes de S7 y cómo lo versionarías."),
        ],
        [
            "raw_score no aparece en ninguna respuesta ni en contracts/openapi.json.",
            "confidence sale con dos decimales y served_at en UTC, ISO 8601 y con sufijo Z.",
            "Ningún error devuelve {\"detail\": ...}, trazas, rutas de ficheros, texto de excepción ni input.",
            "Las rutas lanzan errores de dominio y los manejadores deciden el status; no hay HTTPException en el dominio.",
            "/docs documenta 400, 422 y 503 con ErrorResponse, tags en el router y tres ejemplos de cuerpo.",
            "Los tests propios usan dependency_overrides, parametrize y snapshot sin red real; los archivos protegidos quedan intactos.",
        ],
        [
            ("Contrato de salida tipado y filtrado (S9.1)", "2,5"),
            ("Errores consistentes y seguros (S9.2)", "3"),
            ("OpenAPI útil para un consumidor (S9.3)", "2"),
            ("Tests propios con intención (S9.4)", "2"),
            ("Calidad y nota de compatibilidad", "0,5"),
        ],
        [
            (
                "# Preparación\n"
                "cd semana9/modules/09-api-professional/exercises/02-wine-api-hardening/problem/starter\n"
                "uv sync --locked\n"
                "uv run pytest -q\n"
                "grep -rn \"TODO S9\" src tests"
            ),
            (
                "# Checkpoint por paso\n"
                "uv run pytest -q tests/test_s9_1_output_contract.py\n"
                "uv run pytest -q tests/test_s9_2_errors.py\n"
                "uv run pytest -q tests/test_s9_3_openapi.py\n"
                "uv run pytest -q tests/test_s9_4_student.py"
            ),
            (
                "# Contrato y calidad\n"
                "uv run python -m wine_api.export_openapi\n"
                "uv run ruff check .\n"
                "uv run ruff format --check ."
            ),
            (
                "# API local (Bash) y modelo no disponible\n"
                "uv run fastapi dev\n"
                "WINE_API_MODE=unavailable uv run fastapi dev"
            ),
            "# PowerShell\n$env:WINE_API_MODE=\"unavailable\"; uv run fastapi dev",
        ],
        [
            "No modifiques predictor.py, request_id.py, dependencies.py ni los tests de S9.1-S9.3; si un test parece incorrecto, coméntalo con el docente.",
            "No añadas autenticación ni API keys: la protección de endpoints llega en S10 y estos tests serán su red de seguridad.",
            "Sigue la skill de FastAPI del repositorio: tipos de retorno, Annotated, parámetros comunes en el APIRouter y def para código bloqueante.",
            "La solución de referencia se consulta después de la entrega.",
        ],
        [
            "semana9/modules/09-api-professional/exercises/02-wine-api-hardening/README.md",
            "semana9/modules/09-api-professional/exercises/02-wine-api-hardening/problem/starter/README.md",
        ],
    ),
]


def generate(assignment_data: Assignment) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = (
        f"semana{assignment_data.week:02d}_clase{assignment_data.class_number:02d}_"
        f"assignment.pdf"
    )
    output = OUTPUT_DIR / filename
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=22 * mm,
        title=f"Operación de Modelos - Semana {assignment_data.week} Clase {assignment_data.class_number}",
        author="Comillas ICAI - MUIAAp",
        subject=assignment_data.title,
    )
    doc.assignment = assignment_data
    doc.build(
        build_story(assignment_data),
        onFirstPage=header_footer,
        onLaterPages=header_footer,
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate assignment handouts")
    parser.add_argument(
        "--week",
        type=int,
        help="Generate only the assignments for this week",
    )
    args = parser.parse_args()

    selected = (
        ASSIGNMENTS
        if args.week is None
        else [item for item in ASSIGNMENTS if item.week == args.week]
    )
    if not selected:
        parser.error(f"no assignments found for week {args.week}")
    for assignment_data in selected:
        print(generate(assignment_data))


if __name__ == "__main__":
    main()
