import datetime
import pytest
from app.agent import root_agent, PLANOS_DIR, SKILLS_DIR

@pytest.mark.asyncio
async def test_root_agent_configuration():
    assert root_agent.name == "agente_estudos"
    
    # Verifica que a data de hoje está na instrução
    hoje_fmt = datetime.date.today().strftime("%d/%m/%Y")
    assert hoje_fmt in root_agent.instruction
    
    # Verifica caminhos de skills e planos
    assert SKILLS_DIR.exists()
    assert (SKILLS_DIR / "plano-de-estudos" / "SKILL.md").exists()
    assert PLANOS_DIR.exists()

    # Verifica as ferramentas expostas
    tools = await root_agent.canonical_tools()
    tool_names = [t.name for t in tools]
    
    # Apenas ReadFile e WriteFile devem vir do EnvironmentToolset
    assert "ReadFile" in tool_names
    assert "WriteFile" in tool_names
    assert "Execute" not in tool_names
    assert "EditFile" not in tool_names
    
    # Ferramentas do SkillToolset
    assert "load_skill" in tool_names
    assert "load_skill_resource" in tool_names
