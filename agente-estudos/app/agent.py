# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
from pathlib import Path
from typing import Any, Optional

from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.environment import LocalEnvironment
from google.adk.models import Gemini
from google.adk.skills import load_skills_from_dir
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.environment import EnvironmentToolset
from google.adk.tools.skill_toolset import SkillToolset
from google.genai import types

MODEL = os.getenv("MODEL", "gemini-3.8-flash")

# Caminhos para as skills e a pasta de persistência de planos
APP_DIR = Path(__file__).resolve().parent
SKILLS_DIR = APP_DIR / "skills"
PLANOS_DIR = APP_DIR.parent / "planos"
PLANOS_DIR.mkdir(parents=True, exist_ok=True)

# Data de hoje para orientação temporal do agente
hoje = datetime.date.today()
dias_semana = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]
dia_nome = dias_semana[hoje.weekday()]
hoje_fmt = hoje.strftime("%d/%m/%Y")

INSTRUCTION = f"""Hoje é {dia_nome}, {hoje_fmt}.

Você é um mentor especialista em organização e planejamento de estudos.
Seu objetivo é ajudar as pessoas a organizarem seus estudos criando planos personalizados, estruturados com técnicas de aprendizagem acelerada, revisão espaçada e uma agenda exportável para o Google Agenda (CSV).

Use a skill 'plano-de-estudos' para guiar todo o seu atendimento.

REGRAS FUNDAMENTAIS:
1. Regra de Ativação (Gating): Antes de montar qualquer plano, verifique se a conversa já contém todas as informações obrigatórias:
   - Objetivo: o que quer aprender e para quê
   - Prazo: data de início e data-alvo
   - Disponibilidade: dias da semana e horas por dia (com horário)
   - Nível atual no assunto
   Se faltar alguma dessas informações, NÃO chame a ferramenta 'load_skill_resource' e não monte o plano ainda. Envie uma única mensagem, amigável e direta, perguntando apenas o que falta.
2. Montagem do Plano: Quando todas as informações estiverem preenchidas, use 'load_skill_resource' para carregar os recursos da skill ('references/workflow.md', 'references/tecnicas.md', 'assets/plano_template.md') e monte o plano completo seguindo estritamente as regras de cálculo e distribuição.
3. Exportação da Agenda: Salve o cronograma de estudos em formato CSV usando a ferramenta 'WriteFile' no caminho relativo 'plano-de-estudos.csv', com a primeira linha exata:
   Subject,Start Date,Start Time,End Date,End Time,Description
4. Replanejamento: Em caso de revisões ou ajustes solicitados pelo usuário, leia o arquivo atual se necessário com 'ReadFile', refaça o cronograma e sobrescreva o arquivo inteiro com 'WriteFile'.
"""

# Carregamento da skill via SkillToolset
skills = load_skills_from_dir(SKILLS_DIR)
skill_toolset = SkillToolset(skills=skills)


class RestrictedEnvironmentToolset(EnvironmentToolset):
    """EnvironmentToolset restrito para expor apenas ReadFile e WriteFile."""

    def __init__(self, *, environment: LocalEnvironment, **kwargs: Any) -> None:
        super().__init__(
            environment=environment,
            tool_filter=["ReadFile", "WriteFile"],
            **kwargs,
        )

    async def get_tools(
        self, readonly_context: Optional[ReadonlyContext] = None
    ) -> list[BaseTool]:
        tools = await super().get_tools(readonly_context)
        return [t for t in tools if t.name in ("ReadFile", "WriteFile")]


# Configuração do LocalEnvironment na pasta planos/
env = LocalEnvironment(working_dir=PLANOS_DIR)
env_toolset = RestrictedEnvironmentToolset(environment=env)

root_agent = Agent(
    # Keep in sync with create_params.root_agent_name in agents-cli-manifest.yaml:
    name="agente_estudos",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[skill_toolset, env_toolset],
)

app = App(
    root_agent=root_agent,
    name="app",
)
