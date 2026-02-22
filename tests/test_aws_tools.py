from unittest.mock import MagicMock, patch


class TestCreateBotoClientTool:
    def test_create_boto_client_with_profile(self):
        from src.tools.aws_tools import CreateBotoClientTool

        tool_instance = CreateBotoClientTool(profile="test-profile")
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        with patch("src.tools.aws_tools.boto3.Session", return_value=mock_session):
            result = tool_instance.create_boto_client("s3")

        mock_session.client.assert_called_once_with("s3")
        assert result == mock_client

    def test_create_boto_client_without_profile(self):
        from src.tools.aws_tools import CreateBotoClientTool

        tool_instance = CreateBotoClientTool(profile=None)
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        with patch("src.tools.aws_tools.boto3.Session", return_value=mock_session):
            result = tool_instance.create_boto_client("ec2")

        mock_session.client.assert_called_once_with("ec2")
        assert result == mock_client

    def test_create_boto_client_returns_boto_client(self):
        from src.tools.aws_tools import CreateBotoClientTool

        tool_instance = CreateBotoClientTool(profile="my-profile")
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        with patch("src.tools.aws_tools.boto3.Session", return_value=mock_session):
            result = tool_instance.create_boto_client("dynamodb")

        assert result is mock_client

    def test_tool_decorator_creates_valid_tool(self):
        from src.tools.aws_tools import CreateBotoClientTool

        tool_instance = CreateBotoClientTool(profile="test-profile")
        decorated_tool = tool_instance.as_tool()

        assert callable(decorated_tool)
        assert hasattr(decorated_tool, "name")
        assert hasattr(decorated_tool, "description")

    def test_tool_uses_profile_from_constructor(self):
        from src.tools.aws_tools import CreateBotoClientTool

        tool = CreateBotoClientTool("my-profile")
        assert tool.profile == "my-profile"

    def test_tool_uses_none_when_no_profile(self):
        from src.tools.aws_tools import CreateBotoClientTool

        tool = CreateBotoClientTool(None)
        assert tool.profile is None
