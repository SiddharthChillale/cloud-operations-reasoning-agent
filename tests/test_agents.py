from unittest.mock import MagicMock, patch


class TestCoraAgent:
    def test_cora_agent_without_aws_profile(self):
        with (
            patch("src.agents.aws_agent.get_config") as mock_get_config,
            patch("src.agents.aws_agent.create_model") as mock_create_model,
            patch("src.agents.aws_agent.create_boto_client_tool") as mock_create_tool,
        ):
            mock_config = MagicMock()
            mock_config.has_aws_profile.return_value = False
            mock_get_config.return_value = mock_config

            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            from agents.aws_agent import cora_agent

            agent = cora_agent()

            mock_create_tool.assert_not_called()
            assert "final_answer" in agent.tools
            assert agent.model == mock_model

    def test_cora_agent_model_configuration(self):
        with (
            patch("src.agents.aws_agent.get_config") as mock_get_config,
            patch("src.agents.aws_agent.create_model") as mock_create_model,
        ):
            mock_config = MagicMock()
            mock_config.has_aws_profile.return_value = False
            mock_get_config.return_value = mock_config

            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            from agents.aws_agent import cora_agent

            agent = cora_agent()

            assert agent.model == mock_model
            assert isinstance(agent.tools, dict)
            assert agent.additional_authorized_imports == ["botocore.exceptions"]

    def test_cora_agent_has_additional_authorized_imports(self):
        with (
            patch("src.agents.aws_agent.get_config") as mock_get_config,
            patch("src.agents.aws_agent.create_model") as mock_create_model,
        ):
            mock_config = MagicMock()
            mock_config.has_aws_profile.return_value = False
            mock_get_config.return_value = mock_config

            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            from agents.aws_agent import cora_agent

            agent = cora_agent()

            assert "botocore.exceptions" in agent.additional_authorized_imports

    def test_cora_agent_tools_added_when_profile_exists(self):
        with (
            patch("src.agents.aws_agent.get_config") as mock_get_config,
            patch("src.agents.aws_agent.create_model") as mock_create_model,
        ):
            mock_config = MagicMock()
            mock_config.has_aws_profile.return_value = True
            mock_get_config.return_value = mock_config

            mock_model = MagicMock()
            mock_create_model.return_value = mock_model

            from agents.aws_agent import cora_agent
            from src.tools import create_boto_client_tool

            tool = create_boto_client_tool()
            agent = cora_agent()

            assert tool.name in agent.tools
