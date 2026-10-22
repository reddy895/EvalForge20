"""AWS Bedrock inference provider adapter."""


from src.evalforge.core.config import get_settings
from src.evalforge.core.errors import ProviderError
from src.evalforge.providers.base import BaseProvider
from src.evalforge.providers.schemas import (
    BenchmarkScoreItem,
    InferenceRequest,
    InferenceResponse,
    ModelInfo,
    ModelPricingItem,
    ProviderCapabilities,
)


def get_bedrock_models() -> list[ModelInfo]:
    return [
        ModelInfo(
            id="bedrock:anthropic.claude-3-5-sonnet-20241022-v2:0",
            name="Claude 3.5 Sonnet (AWS Bedrock)",
            provider="bedrock",
            model_identifier="anthropic.claude-3-5-sonnet-20241022-v2:0",
            family="Claude",
            parameter_count="Large frontier",
            context_window=200000,
            modalities=["text->text", "image->text"],
            supports_tools=True,
            supports_structured_output=True,
            license="AWS Bedrock Service Terms",
            is_commercial_use_allowed=True,
            release_date="2024-10-22",
            description="Frontier Claude 3.5 Sonnet deployed in AWS VPC with AWS IAM credentials and private PrivateLink.",
            is_local=False,
            is_installed=False,
            is_remote=True,
            benchmarks=[
                BenchmarkScoreItem(benchmark_name="HumanEval", metric="pass@1", score=93.7, source="AWS Bedrock Documentation", verified=True),
            ],
            pricing=ModelPricingItem(input_cost_per_m=3.00, output_cost_per_m=15.00, currency="USD", is_free_local=False, source_url="https://aws.amazon.com/bedrock/pricing/"),
            strengths=["AWS IAM role integration", "Zero data egress out of AWS", "HIPAA eligible"],
            weaknesses=["Requires AWS IAM permissions and Bedrock model access enablement"],
            recommended_tasks=["aws_native_rag", "coding", "enterprise_security"],
        ),
    ]


class BedrockProvider(BaseProvider):
    """AWS Bedrock inference adapter."""

    def __init__(self) -> None:
        settings = get_settings()
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SECRET_ACCESS_KEY
        self.region = settings.AWS_REGION
        super().__init__(
            name="bedrock",
            config={"region": self.region, "has_credentials": bool(self.access_key and self.secret_key)},
            display_name="AWS Bedrock",
            provider_type="cloud",
            implementation_status="configurable_cloud",
            setup_instructions="Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION in your .env file or environment variables.",
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.access_key and self.secret_key)

    async def health_check(self) -> bool:
        return self.is_configured

    async def list_models(self) -> list[ModelInfo]:
        return get_bedrock_models()

    async def get_model_capabilities(self, model_id: str) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_chat=True,
            supports_generation=True,
            supports_streaming=True,
            supports_tools=True,
            supports_structured_output=True,
            supports_system_prompt=True,
            max_context_length=200000,
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        if not self.is_configured:
            raise ProviderError(
                f"Provider 'bedrock' is not configured with AWS credentials. {self.setup_instructions}",
                provider="bedrock",
            )
        # Note: In production without boto3 installed, return informative error or mock payload
        raise ProviderError(
            "AWS Bedrock client requires boto3 and enabled model access in AWS Console. Please install boto3 or configure your AWS credentials.",
            provider="bedrock",
        )
