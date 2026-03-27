# Contributing to AgroLidar

## Setup del entorno

1. Clona el repositorio y entra al directorio del proyecto.
2. Ejecuta `make setup` para instalar dependencias y hooks de pre-commit/pre-push en un solo comando.
3. Verifica que todo esté correcto con `make pre-commit-run`.

## Branching strategy

Usa ramas por tipo de trabajo:

- `feature/*` para nuevas funcionalidades.
- `fix/*` para correcciones de bugs.
- `model/*` para cambios de arquitectura, training o evaluación de modelos.
- `safety/*` para cambios que afecten lógica crítica de seguridad.

Nunca trabajes directamente sobre `main`; abre PR desde tu rama.

## Commit message format (Conventional Commits)

Formato recomendado:

- `feat: add hard-case mining threshold`
- `fix: handle empty point clouds in inference`
- `chore: update pre-commit hooks`
- `ci: add PR quality gate`
- `docs: update safety incident process`

Estructura: `<type>(optional-scope): <description corta en imperativo>`.

## Pre-commit hooks

Qué validan:

- Higiene de archivos (`trailing-whitespace`, `end-of-file-fixer`, YAML/JSON/TOML válidos).
- Bloqueo de archivos grandes y conflictos de merge.
- Bloqueo de commits directos a `main`.
- Lint/format con Ruff y tipado con mypy en módulos Python clave.
- Validación de `configs/*.yaml`.
- En `pre-push`: smoke tests rápidos (`pytest tests/ -x -q --tb=short`).

Comandos útiles:

- Instalar hooks: `make pre-commit-install`
- Correr todos los hooks: `make pre-commit-run`
- Actualizar versiones: `make pre-commit-update`

Bypass solo en emergencia:

- Commit sin hooks: `git commit --no-verify`
- Push sin hooks: `git push --no-verify`

Si usas bypass, documenta la razón en el PR y crea follow-up inmediato.

## Cómo agregar un nuevo experimento

1. Crea una rama `model/*`.
2. Duplica o extiende un config en `configs/` y describe el objetivo del experimento.
3. Corre entrenamiento/evaluación local y guarda artefactos/reportes relevantes.
4. Adjunta o linkea el eval report en el PR.
5. Si agregas dependencias, pínnalas en `requirements.txt`.

## Cómo reportar un safety incident

1. Abre un issue usando el template **Safety incident**.
2. Incluye clases afectadas, condiciones (polvo/lluvia/terreno), frame IDs y evaluación del impacto (FN/FP).
3. Documenta mitigación inmediata y próximos pasos.
4. Escala revisión de cambios críticos con `safety/*` y solicita sign-off.

## PR process y review requirements

1. Asegura que la descripción del PR esté completa (template obligatorio).
2. Completa checklist de lint/test/pre-commit.
3. CI de PR debe pasar (`pr_checks.yml`).
4. CODEOWNERS aplica revisión de `@geromendez199` en áreas críticas.
5. Nunca mergear un PR con incidentes de seguridad no mitigados.

## Definition of Done

### Bug fix
- Reproducción documentada y corregida.
- Tests relevantes pasan.
- Sin regresiones evidentes.

### New feature
- Requisitos funcionales implementados.
- Cobertura mínima de pruebas y docs actualizadas.
- Riesgo de seguridad evaluado.

### Model change
- Métricas antes/después reportadas.
- Eval report adjunto o enlazado.
- Impacto en safety classes explicitado.

### Config change
- Config válido (`pre-commit` y CI en verde).
- `configs/README` actualizado si aplica.
- Compatibilidad con pipeline verificada.

### Pipeline/CI change
- Workflow validado.
- Señales de fallo claras y accionables.
- Sin incrementar innecesariamente tiempos de feedback local.
