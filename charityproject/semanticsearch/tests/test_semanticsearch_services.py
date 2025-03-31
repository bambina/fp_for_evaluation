from unittest.mock import MagicMock, patch

from semanticsearch.services import *


class TestUSEModelService:
    """Test suite for USEModelService."""

    @patch("semanticsearch.services.os.path.exists", return_value=True)
    @patch("semanticsearch.services.hub.load")
    def test_load_model_when_model_dir_exists(self, mock_hub_load, mock_exists):
        """Test that the model is loaded when the directory exists."""
        mock_model = MagicMock()
        mock_hub_load.return_value = mock_model

        USEModelService._model = None
        USEModelService.load_model()

        mock_exists.assert_called_once()
        mock_hub_load.assert_called_once_with(settings.USE_MODEL_DIR)
        assert USEModelService._model == mock_model

    @patch("semanticsearch.services.USEModelService.load_model")
    def test_get_vector_representation_returns_expected_array(self, mock_load_model):
        """Test that get_vector_representation returns the expected vector array."""
        mock_model = MagicMock()
        fake_numpy_array = MagicMock()
        mock_model.return_value.numpy.return_value = fake_numpy_array

        USEModelService._model = mock_model
        result = USEModelService.get_vector_representation(["Hello world"])

        assert result == fake_numpy_array
        mock_model.assert_called_once_with(["Hello world"])
