from typing import Annotated

from pydantic import *

__all__ = (
    # dataclasses
    'dataclasses',
    # functional validators
    'field_validator',
    'model_validator',
    'AfterValidator',
    'BeforeValidator',
    'PlainValidator',
    'WrapValidator',
    'SkipValidation',
    'InstanceOf',
    # JSON Schema
    'WithJsonSchema',
    # functional serializers
    'field_serializer',
    'model_serializer',
    'PlainSerializer',
    'SerializeAsAny',
    'WrapSerializer',
    # config
    'ConfigDict',
    # validate_call
    'validate_call',
    # errors
    'PydanticErrorCodes',
    'PydanticUserError',
    'PydanticSchemaGenerationError',
    'PydanticImportError',
    'PydanticUndefinedAnnotation',
    'PydanticInvalidForJsonSchema',
    # fields
    'AliasPath',
    'AliasChoices',
    'Field',
    'computed_field',
    'PrivateAttr',
    # main
    'BaseModel',
    'create_model',
    # network
    'AnyUrl',
    'AnyHttpUrl',
    'FileUrl',
    'HttpUrl',
    'UrlConstraints',
    'EmailStr',
    'NameEmail',
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'PostgresDsn',
    'CockroachDsn',
    'AmqpDsn',
    'RedisDsn',
    'MongoDsn',
    'KafkaDsn',
    'MySQLDsn',
    'MariaDBDsn',
    'validate_email',
    # types
    'Strict',
    'StrictStr',
    'conbytes',
    'conlist',
    'conset',
    'confrozenset',
    'constr',
    'StringConstraints',
    'ImportString',
    'conint',
    'PositiveInt',
    'NegativeInt',
    'NonNegativeInt',
    'NonPositiveInt',
    'confloat',
    'PositiveFloat',
    'NegativeFloat',
    'NonNegativeFloat',
    'NonPositiveFloat',
    'FiniteFloat',
    'condecimal',
    'condate',
    'UUID1',
    'UUID3',
    'UUID4',
    'UUID5',
    'FilePath',
    'DirectoryPath',
    'NewPath',
    'Json',
    'SecretStr',
    'SecretBytes',
    'StrictBool',
    'StrictBytes',
    'StrictInt',
    'StrictFloat',
    'PaymentCardNumber',
    'ByteSize',
    'PastDate',
    'FutureDate',
    'PastDatetime',
    'FutureDatetime',
    'AwareDatetime',
    'NaiveDatetime',
    'AllowInfNan',
    'EncoderProtocol',
    'EncodedBytes',
    'EncodedStr',
    'Base64Encoder',
    'Base64Bytes',
    'Base64Str',
    'Base64UrlBytes',
    'Base64UrlStr',
    'Tag',
    # pydantic_core
    'ValidationError',
    # custom types
    'CronSchedule',
)

# CronSchedule type
try:
    from croniter import croniter
except ImportError as e:
    raise ImportError('croniter is not installed, run `pip install croniter`') from e

def validate_cron_input(value: str) -> str:
    if not croniter.is_valid(value):
        raise ValueError('Invalid cron schedule')
    return value

CronSchedule = Annotated[
    str,
    # Field(pattern=r'^(?:(?:[1-5]?[0-9]|\*)\s){4}(?:(?:[1-7]|\*)\s)(?:\S+)$', type='string', format='cron', example='*/15 * * * *'),
    AfterValidator(validate_cron_input),
    WithJsonSchema({'type': 'string', 'format': 'cron', 'example': '*/15 * * * *'}),
]
# TODO Create chat_message type (uses ui.chat_message() )

# Header type

# Notice types