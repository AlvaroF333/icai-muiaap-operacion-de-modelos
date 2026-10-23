from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader

MODULE_PATH = Path(__file__).with_name("generate_assignment_pdfs.py")
SPEC = importlib.util.spec_from_file_location("generate_assignment_pdfs", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
pdfs = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pdfs
SPEC.loader.exec_module(pdfs)


MAIN_SNIPPET = """import os

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
"""

TEST_SNIPPET = """import pytest

from env_demo.main import environment_message


@pytest.mark.parametrize("environment", ["dev", "pre", "pro"])
def test_known_environment(environment: str) -> None:
    assert environment.upper() in environment_message(environment)


def test_unknown_environment() -> None:
    with pytest.raises(ValueError, match="APP_ENV"):
        environment_message("local")
"""


def week_two_assignments():
    return [item for item in pdfs.ASSIGNMENTS if item.week == 2]


def week_five_assignments():
    week_five = [item for item in pdfs.ASSIGNMENTS if item.week == 5]

    assert [(item.week, item.class_number) for item in week_five] == [(5, 1), (5, 2)]
    return week_five


def week_seven_assignments():
    week_seven = [item for item in pdfs.ASSIGNMENTS if item.week == 7]

    assert [(item.week, item.class_number) for item in week_seven] == [
        (7, 1),
        (7, 2),
    ]
    return week_seven


def week_seven_class_one_assignment():
    return week_seven_assignments()[0]


def week_seven_class_two_assignment():
    return week_seven_assignments()[1]


def assignment_text(item) -> str:
    values = [
        item.title,
        item.subtitle,
        item.duration,
        item.modality,
        item.prerequisites,
        item.goal,
        *item.context,
        *item.materials,
        *item.acceptance,
        *item.commands,
        *item.notes,
        *item.source_paths,
    ]
    values.extend(value for row in item.tasks for value in row)
    values.extend(value for row in item.deliverables for value in row)
    values.extend(value for row in item.rubric for value in row)
    values.extend(value for snippet in item.task_snippets.values() for value in snippet)
    return "\n".join(values)


def test_only_week_two_assignments_use_task_snippets() -> None:
    week_two = week_two_assignments()

    assert [(item.week, item.class_number) for item in week_two] == [(2, 1), (2, 2)]
    assert week_two[0].task_snippets == {
        4: ("src/env_demo/main.py", MAIN_SNIPPET),
        5: ("tests/test_main.py", TEST_SNIPPET),
    }
    assert week_two[1].task_snippets == {}
    assert all(not item.task_snippets for item in pdfs.ASSIGNMENTS if item.week != 2)
    assert pdfs.SNIPPET_CODE.fontSize >= 6.5
    assert pdfs.SNIPPET_CODE.leading >= 7.4


def test_week_two_definitions_and_rubrics() -> None:
    first, second = week_two_assignments()

    assert first.title == "Del directorio vacio al proyecto reproducible"
    assert first.duration == "45-50 min"
    assert first.modality == "Parejas, terminal Bash"
    assert second.title == "De la practica de S1 a un proyecto revisable"
    assert second.duration == "120 min"
    assert second.modality == "Parejas, fork propio"
    assert all(sum(int(points) for _, points in item.rubric) == 10 for item in (first, second))


def test_week_two_is_bash_only_and_avoids_out_of_scope_tools() -> None:
    first, second = week_two_assignments()
    combined = assignment_text(first) + "\n" + assignment_text(second)

    for forbidden in (
        "PowerShell",
        "Copy-Item",
        "New-Item",
        "gh ",
        "Databricks",
        "MLflow",
        "Registry",
        "XGBoost",
        "model.joblib",
    ):
        assert forbidden not in combined

    assignment_and_tasks = "\n".join(
        [second.goal, *(value for task in second.tasks for value in task)]
    )
    criteria_and_notes = "\n".join([*second.acceptance, *second.notes])
    assert "pull request (PR)" in assignment_and_tasks
    assert "pull request (PR)" in criteria_and_notes

    gitignore_command = (
        "printf '.venv/\\n__pycache__/\\n.pytest_cache/\\n.ruff_cache/\\n' "
        "> .gitignore"
    )
    assert any(gitignore_command in command for command in first.commands)
    assert "Crea .gitignore" in assignment_text(first)


@pytest.fixture()
def generated_week_two(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output_dir = tmp_path / "assignments"
    monkeypatch.setattr(pdfs, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--week", "2"])

    pdfs.main()

    generated = sorted(output_dir.glob("*.pdf"))
    assert [path.name for path in generated] == [
        "semana02_clase01_assignment.pdf",
        "semana02_clase02_assignment.pdf",
    ]
    return generated


def test_unknown_week_exits_with_a_clear_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_dir = tmp_path / "assignments"
    monkeypatch.setattr(pdfs, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--week", "99"])

    with pytest.raises(SystemExit) as exc_info:
        pdfs.main()

    assert exc_info.value.code == 2
    assert "no assignments found for week 99" in capsys.readouterr().err
    assert not output_dir.exists()


def test_week_filter_generates_only_two_a4_two_page_pdfs(generated_week_two) -> None:
    expected_width, expected_height = pdfs.A4

    for path in generated_week_two:
        reader = PdfReader(path)
        assert len(reader.pages) == 2
        for page in reader.pages:
            assert float(page.mediabox.width) == pytest.approx(expected_width, abs=0.1)
            assert float(page.mediabox.height) == pytest.approx(expected_height, abs=0.1)


def test_snippet_labels_stay_with_their_source(generated_week_two) -> None:
    first = PdfReader(generated_week_two[0])
    pages = [page.extract_text() or "" for page in first.pages]

    assert any("src/env_demo/main.py" in page and "import os" in page for page in pages)
    assert any("tests/test_main.py" in page and "import pytest" in page for page in pages)


def test_acceptance_section_is_not_split_between_pages(generated_week_two) -> None:
    expected_last_item = (
        "README permite repetir el trabajo desde un checkout limpio.",
        "El pull request (PR) muestra 2-3 commits y tiene como base main del fork propio.",
    )

    for path, final_item in zip(generated_week_two, expected_last_item):
        pages = [page.extract_text() or "" for page in PdfReader(path).pages]
        assert any(
            "6. Criterios de aceptacion" in page and final_item in page
            for page in pages
        )


def test_generated_week_two_has_sections_commands_and_target_length(
    generated_week_two,
) -> None:
    extracted = {
        path.name: "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        for path in generated_week_two
    }

    for text in extracted.values():
        for section_number in range(1, 10):
            assert re.search(rf"(?m)^{section_number}\. ", text)
        words = re.findall(r"\b[\wÀ-ÿ][\wÀ-ÿ./-]*\b", text)
        assert 500 <= len(words) <= 650

    first = extracted["semana02_clase01_assignment.pdf"]
    first_normalized = re.sub(r"\s+", " ", first)
    for critical in (
        "git init",
        "uv init --package --vcs none .",
        "uv add rich",
        "uv add --dev pytest ruff",
        "printf '.venv/\\n__pycache__/\\n.pytest_cache/\\n.ruff_cache/\\n' > .gitignore",
        "APP_ENV=dev uv run python -m env_demo.main",
        "APP_ENV=pre uv run python -m env_demo.main",
        "APP_ENV=pro uv run python -m env_demo.main",
        "uv run pytest",
        "uv run ruff check .",
        "git log --oneline",
        "git ls-files .venv",
        "bootstrap uv project",
        "add environment-aware command",
        "add tests and usage documentation",
        "VALID_ENVIRONMENTS",
        'environment_message("local")',
        "sin remoto",
    ):
        assert critical in first_normalized

    second = extracted["semana02_clase02_assignment.pdf"]
    second_normalized = re.sub(r"\s+", " ", second)
    for critical in (
        "semana2/starter/WineQT.csv",
        "semana2/starter/train.py",
        "semana2/starter/test_train.py",
        "feature/s2-wine-project",
        "uv init --package --vcs none --name wine-quality semana2/wine-quality-project",
        "uv add pandas scikit-learn",
        "uv add --dev pytest ruff",
        "data/raw/WineQT.csv",
        "src/wine_quality/train.py",
        "tests/test_train.py",
        "uv sync --locked",
        "uv run --frozen python -m wine_quality.train",
        "uv run --frozen pytest",
        "uv run --frozen ruff check .",
        "main del mismo fork",
        "nunca el repositorio docente",
        "pull request (PR)",
    ):
        assert critical in second_normalized


def test_week_five_definitions_and_rubrics() -> None:
    first, second = week_five_assignments()

    assert first.title == "Del formulario a la inferencia: miniapp Churn"
    assert first.duration == "60 min"
    assert "guiada" in first.modality.lower()
    assert "Parejas" in first.modality
    assert second.title == "Del bundle S4 al frontal Wine"
    assert second.duration == "120 min"
    assert "Parejas" in second.modality
    assert first.rubric == [
        ("Formulario y widgets", "2"),
        ("Submit 0/1", "2"),
        ("Separación UI/inferencia", "2"),
        ("Resultado y error", "2"),
        ("Tests y QA", "2"),
    ]
    assert second.rubric == [
        ("Bundle real y contrato Wine", "2"),
        ("Formulario y submit", "2"),
        ("Frontera gateway", "2"),
        ("Resultado y error", "2"),
        ("Reproducibilidad, tests y QA", "2"),
    ]


def test_week_five_timelines_match_the_final_readmes() -> None:
    first, second = week_five_assignments()

    assert [title for title, _ in first.tasks] == [
        "Lee el contrato y anticipa dos predicciones · 0–10 min",
        "Construye el formulario · 10–25 min",
        "Conecta submit y predict() · 25–35 min",
        "Presenta resultado y error · 35–45 min",
        "Ejecuta los tests · 45–55 min",
        "Cierra QA y puente · 55–60 min",
    ]
    assert [title for title, _ in second.tasks] == [
        "Localiza y valida el bundle · 0–15 min",
        "Construye los widgets · 15–35 min",
        "Completa formulario y submit · 35–55 min",
        "Revisa la frontera gateway · 55–75 min",
        "Presenta el resultado · 75–90 min",
        "Prueba bundle ausente · 90–105 min",
        "Ejecuta tests y QA · 105–115 min",
        "Documenta ejecución y límites · 115–120 min",
    ]


def test_week_five_class_one_is_the_guided_churn_miniapp() -> None:
    first, _ = week_five_assignments()
    content = assignment_text(first)

    for required in (
        "semana5/modules/05-streamlit-basic-model-ui/exercises/01-churn-streamlit/problem/starter",
        "predict()",
        "tenure_months",
        "monthly_spend_eur",
        "support_calls",
        "has_annual_contract",
        "st.form",
        "st.form_submit_button",
        "cero llamadas",
        "una llamada",
        "label",
        "risk_score",
        "explanation",
        "ValueError",
        "app.py",
        "13 pruebas",
        "cuatro casos",
        "uv sync",
        "uv run python -m pytest -q",
        "uv run ruff check app.py src tests",
        "uv run ruff format --check app.py src tests",
        "uv run streamlit run app.py",
    ):
        assert required in content

    for forbidden in (
        "ui_schema.py",
        "FIELD_SPECS",
        "MODEL_UI_BUNDLE",
        "DemoGateway",
        "quality_band",
        "model_version",
        "preprocessing_version",
        "once campos",
    ):
        assert forbidden not in content


def test_week_five_class_two_uses_only_the_real_s4_wine_bundle() -> None:
    _, second = week_five_assignments()
    content = assignment_text(second)

    for required in (
        "semana5/modules/05-streamlit-basic-model-ui/exercises/02-first-streamlit/problem/starter",
        "FIELD_SPECS",
        "once campos",
        "collect_values()",
        "render_prediction()",
        "st.form",
        "st.form_submit_button",
        "gateway.predict(values)",
        "cero llamadas",
        "una llamada",
        "quality_band",
        "confidence",
        "model_version",
        "preprocessing_version",
        "MODEL_UI_BUNDLE",
        "manifest.json",
        "model.joblib",
        "bundle ausente o inválido",
        "inferencia inválida",
        "27 pruebas",
        "cuatro casos",
        "uv sync",
        "$env:MODEL_UI_BUNDLE = 'RUTA_AL_BUNDLE_DE_S4'",
        "uv run python -m pytest -q",
        "uv run ruff check app.py src tests",
        "uv run ruff format --check app.py src tests",
        "uv run --with 'streamlit>=1.40,<2.0' streamlit run app.py",
    ):
        assert required in content

    for forbidden in (
        "DemoGateway",
        "modo demo",
        "tenure_months",
        "monthly_spend_eur",
        "support_calls",
        "has_annual_contract",
    ):
        assert forbidden not in content

    assert "churn" not in content.lower()
    assert any(
        title == "Configuración del bundle" and "MODEL_UI_BUNDLE" in description
        for title, description in second.deliverables
    )
    assert any(
        title == "Evidencias"
        and "bundle real" in description
        and "bundle ausente" in description
        for title, description in second.deliverables
    )


@pytest.fixture()
def generated_week_five(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output_dir = tmp_path / "assignments"
    monkeypatch.setattr(pdfs, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--week", "5"])

    pdfs.main()

    generated = sorted(output_dir.glob("*.pdf"))
    assert [path.name for path in generated] == [
        "semana05_clase01_assignment.pdf",
        "semana05_clase02_assignment.pdf",
    ]
    return generated


def test_generated_week_five_is_two_a4_two_page_pdfs(generated_week_five) -> None:
    expected_width, expected_height = pdfs.A4

    for path in generated_week_five:
        reader = PdfReader(path)
        assert len(reader.pages) == 2
        for page in reader.pages:
            assert float(page.mediabox.width) == pytest.approx(expected_width, abs=0.1)
            assert float(page.mediabox.height) == pytest.approx(
                expected_height, abs=0.1
            )

        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert re.findall(r"(?m)^([1-9])\. ", extracted) == [
            str(section_number) for section_number in range(1, 10)
        ]


def test_generated_week_five_text_matches_the_two_final_practices(
    generated_week_five,
) -> None:
    extracted_by_name = {
        path.name: re.sub(
            r"\s+",
            " ",
            "\n".join(page.extract_text() or "" for page in PdfReader(path).pages),
        )
        for path in generated_week_five
    }

    churn = extracted_by_name["semana05_clase01_assignment.pdf"]
    assert "Del formulario a la inferencia: miniapp Churn" in churn
    assert "DURACION" in churn
    assert "60 min" in churn
    assert (
        "semana5/modules/05-streamlit-basic-model-ui/exercises/01-churn-streamlit/problem/starter"
        in churn
    )
    for required in (
        "st.form",
        "st.form_submit_button",
        "cero llamadas",
        "una llamada",
        "label, risk_score y explanation",
        "13 pruebas",
        "cuatro casos",
        "uv sync",
        "uv run python -m pytest -q",
        "uv run ruff check app.py src tests",
        "uv run ruff format --check app.py src tests",
        "uv run streamlit run app.py",
        "Lee el contrato y anticipa dos predicciones · 0–10 min",
        "Construye el formulario · 10–25 min",
        "Conecta submit y predict() · 25–35 min",
        "Presenta resultado y error · 35–45 min",
        "Ejecuta los tests · 45–55 min",
        "Cierra QA y puente · 55–60 min",
        "Formulario y widgets",
        "Submit 0/1",
        "Separación UI/inferencia",
        "Resultado y error",
        "Tests y QA",
    ):
        assert required in churn
    for forbidden in (
        "ui_schema",
        "FIELD_SPECS",
        "MODEL_UI_BUNDLE",
        "DemoGateway",
        "quality_band",
    ):
        assert forbidden not in churn

    wine = extracted_by_name["semana05_clase02_assignment.pdf"]
    assert "Del bundle S4 al frontal Wine" in wine
    assert "DURACION" in wine
    assert "120 min" in wine
    assert (
        "semana5/modules/05-streamlit-basic-model-ui/exercises/02-first-streamlit/problem/starter"
        in wine
    )
    for required in (
        "MODEL_UI_BUNDLE",
        "manifest.json",
        "model.joblib",
        "once campos",
        "FIELD_SPECS",
        "collect_values()",
        "render_prediction()",
        "gateway.predict(values)",
        "quality_band, confidence, model_version y preprocessing_version",
        "bundle ausente o inválido",
        "inferencia inválida",
        "27 pruebas",
        "cuatro casos",
        "uv sync",
        "$env:MODEL_UI_BUNDLE = 'RUTA_AL_BUNDLE_DE_S4'",
        "uv run python -m pytest -q",
        "uv run ruff check app.py src tests",
        "uv run ruff format --check app.py src tests",
        "uv run --with 'streamlit>=1.40,<2.0' streamlit run app.py",
        "Localiza y valida el bundle · 0–15 min",
        "Construye los widgets · 15–35 min",
        "Completa formulario y submit · 35–55 min",
        "Revisa la frontera gateway · 55–75 min",
        "Presenta el resultado · 75–90 min",
        "Prueba bundle ausente · 90–105 min",
        "Ejecuta tests y QA · 105–115 min",
        "Documenta ejecución y límites · 115–120 min",
        "Configuración del bundle",
        "bundle real y bundle ausente",
        "Bundle real y contrato Wine",
        "Formulario y submit",
        "Frontera gateway",
        "Resultado y error",
        "Reproducibilidad, tests y QA",
    ):
        assert required in wine
    for forbidden in (
        "DemoGateway",
        "modo demo",
        "churn",
        "tenure_months",
        "monthly_spend_eur",
        "support_calls",
        "has_annual_contract",
    ):
        assert forbidden not in wine


def test_week_seven_class_one_definition_and_rubric() -> None:
    item = week_seven_class_one_assignment()

    assert item.title == "De curl a un cliente Python"
    assert item.duration == "75-90 min"
    assert "Parejas" in item.modality
    assert [int(points) for _, points in item.rubric] == [3, 2, 2, 2, 1]
    assert sum(int(points) for _, points in item.rubric) == 10


def test_week_seven_class_one_scope_and_contract() -> None:
    content = assignment_text(week_seven_class_one_assignment())

    for required in (
        "pump-maintenance-api",
        "GET /health",
        "POST /v1/predictions",
        "json=payload",
        "raise_for_status",
        "timeout",
        "ConnectionError",
        "PredictionClientError",
        "cinco pruebas",
        "request_id",
        "422",
    ):
        assert required in content

    for forbidden in (
        "MODEL_API_URL",
        "PredictionController",
        'json={"features":',
        "streamlit run",
    ):
        assert forbidden not in content


def test_week_seven_class_one_commands_use_module_root() -> None:
    commands = week_seven_class_one_assignment().commands

    assert commands[0].startswith(
        "# Terminal 1 - servidor\n"
        "cd semana7/modules/07-http-rest-clients\n"
        "uv sync\n"
    )
    assert "examples/pump-maintenance-api/server.py" in commands[0]
    assert commands[1].startswith(
        "# Terminal 2 - Bash o Git Bash\n"
        "cd semana7/modules/07-http-rest-clients\n"
    )
    assert "--data-binary @examples/pump-maintenance-api/samples/" in commands[1]
    assert "python -m unittest discover" in commands[2]


def test_week_seven_class_two_definition_and_rubric() -> None:
    item = week_seven_class_two_assignment()

    assert item.title == "De gateway local a cliente HTTP"
    assert item.duration == "120 min"
    assert "Parejas" in item.modality
    assert [int(points) for _, points in item.rubric] == [2, 2, 2, 2, 2]
    assert sum(int(points) for _, points in item.rubric) == 10


def test_week_seven_class_two_scope_and_contract() -> None:
    content = assignment_text(week_seven_class_two_assignment())

    for required in (
        "HttpInferenceGateway",
        "MODEL_API_URL",
        "POST /v1/predictions",
        "PredictionPayload",
        "timeout",
        "422",
        "503",
        "S8",
    ):
        assert required in content

    for forbidden in ("FastAPI", "Uvicorn", "TestClient", "API key"):
        assert forbidden not in content


def test_week_seven_commands_separate_server_and_app_terminals() -> None:
    commands = week_seven_class_two_assignment().commands

    assert commands[0] == (
        "# Terminal 1 - servidor\n"
        "cd semana7/modules/07-http-rest-clients\n"
        "uv sync\n"
        "uv run python examples/wine-quality-api/server.py"
    )
    assert commands[1].startswith(
        "# Terminal 2 - app\n"
        "cd semana7/modules/07-http-rest-clients/exercises/"
        "03-wine-http-gateway/problem/starter\n"
    )


def test_week_seven_commands_include_bash_and_powershell_environment() -> None:
    commands = week_seven_class_two_assignment().commands

    assert (
        "# Bash\n"
        "MODEL_API_URL=http://127.0.0.1:8000 uv run streamlit run app.py"
    ) in commands
    assert (
        "# PowerShell\n"
        '$env:MODEL_API_URL="http://127.0.0.1:8000"; '
        "uv run streamlit run app.py"
    ) in commands


@pytest.fixture()
def generated_week_seven(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output_dir = tmp_path / "assignments"
    monkeypatch.setattr(pdfs, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--week", "7"])

    pdfs.main()

    generated = sorted(output_dir.glob("*.pdf"))
    assert [path.name for path in generated] == [
        "semana07_clase01_assignment.pdf",
        "semana07_clase02_assignment.pdf",
    ]
    return generated


def test_generated_week_seven_are_two_a4_pages_with_nine_sections(
    generated_week_seven,
) -> None:
    expected_width, expected_height = pdfs.A4

    for output in generated_week_seven:
        reader = PdfReader(output)
        assert len(reader.pages) == 2
        for page in reader.pages:
            assert float(page.mediabox.width) == pytest.approx(
                expected_width, abs=0.1
            )
            assert float(page.mediabox.height) == pytest.approx(
                expected_height, abs=0.1
            )

        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert re.findall(r"(?m)^([1-9])\. ", extracted) == [
            str(section_number) for section_number in range(1, 10)
        ]


def test_root_readme_links_week_seven_assignments() -> None:
    readme = (MODULE_PATH.parents[1] / "README.md").read_text("utf-8")

    assert (
        "| S7 | [Assignment 7.1](assignments/semana07_clase01_assignment.pdf) "
        "| [Assignment 7.2](assignments/semana07_clase02_assignment.pdf) |"
    ) in readme


def week_nine_assignments():
    week_nine = [item for item in pdfs.ASSIGNMENTS if item.week == 9]

    assert [(item.week, item.class_number) for item in week_nine] == [
        (9, 1),
        (9, 2),
    ]
    return week_nine


def test_week_nine_class_one_covers_the_four_microexercises() -> None:
    item = week_nine_assignments()[0]
    content = assignment_text(item)

    assert [int(points) for _, points in item.rubric] == [2, 3, 2, 2, 1]
    for required in (
        "M1",
        "M2",
        "M3",
        "M4",
        "serialization_demo.py",
        "errors_demo.py",
        "openapi_demo.py",
        "tests/test_examples.py",
        "response_model",
        "TU_SECRETO",
        "dependency_overrides",
        "raise_server_exceptions=False",
        "no_income",
    ):
        assert required in content
    assert item.commands[0].startswith(
        "# Terminal 1 - demos\n"
        "cd semana9/modules/09-api-professional\n"
        "uv sync --locked\n"
    )


def test_week_nine_class_two_follows_the_workshop_without_the_solution() -> None:
    item = week_nine_assignments()[1]
    content = assignment_text(item)

    assert item.duration == "120 min"
    assert [points for _, points in item.rubric] == ["2,5", "3", "2", "2", "0,5"]
    for required in (
        "S9.1",
        "S9.2",
        "S9.3",
        "S9.4",
        "1.1.0",
        "POST /v1/predictions",
        "contracts/openapi.json",
        "dependency_overrides",
        "raw_score",
        "400, 422 y 503",
        "WINE_API_MODE=unavailable",
        "S10",
    ):
        assert required in content
    for forbidden in ("solutions/", "field_serializer", "model_validate"):
        assert forbidden not in content


@pytest.fixture()
def generated_week_nine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    output_dir = tmp_path / "assignments"
    monkeypatch.setattr(pdfs, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(sys, "argv", [str(MODULE_PATH), "--week", "9"])

    pdfs.main()

    generated = sorted(output_dir.glob("*.pdf"))
    assert [path.name for path in generated] == [
        "semana09_clase01_assignment.pdf",
        "semana09_clase02_assignment.pdf",
    ]
    return generated


def test_generated_week_nine_are_two_a4_pages_with_nine_sections(
    generated_week_nine,
) -> None:
    for output in generated_week_nine:
        reader = PdfReader(output)
        assert len(reader.pages) == 2

        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert re.findall(r"(?m)^([1-9])\. ", extracted) == [
            str(section_number) for section_number in range(1, 10)
        ]


def test_root_readme_links_week_nine_assignments() -> None:
    readme = (MODULE_PATH.parents[1] / "README.md").read_text("utf-8")

    assert (
        "| S9 | [Assignment 9.1](assignments/semana09_clase01_assignment.pdf) "
        "| [Assignment 9.2](assignments/semana09_clase02_assignment.pdf) |"
    ) in readme
