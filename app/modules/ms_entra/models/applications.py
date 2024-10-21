from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from core.utils.datetime import *
"""
{
  "addIns": [{"@odata.type": "microsoft.graph.addIn"}],
  "api": {"@odata.type": "microsoft.graph.apiApplication"},
  "appId": "String",
  "applicationTemplateId": "String",
  "appRoles": [{"@odata.type": "microsoft.graph.appRole"}],
  "certification": {"@odata.type": "microsoft.graph.certification"},
  "createdDateTime": "String (timestamp)",
  "deletedDateTime": "String (timestamp)",
  "disabledByMicrosoftStatus": "String",
  "displayName": "String",
  "groupMembershipClaims": "String",
  "id": "String (identifier)",
  "identifierUris": ["String"],
  "info": {"@odata.type": "microsoft.graph.informationalUrl"},
  "isDeviceOnlyAuthSupported": false,
  "isFallbackPublicClient": false,
  "keyCredentials": [{"@odata.type": "microsoft.graph.keyCredential"}],
  "logo": "Stream",
  "notes": "String",
  "oauth2RequiredPostResponse": false,
  "optionalClaims": {"@odata.type": "microsoft.graph.optionalClaims"},
  "parentalControlSettings": {"@odata.type": "microsoft.graph.parentalControlSettings"},
  "passwordCredentials": [{"@odata.type": "microsoft.graph.passwordCredential"}],
  "publicClient": {"@odata.type": "microsoft.graph.publicClientApplication"},
  "publisherDomain": "String",
  "requestSignatureVerification": {"@odata.type": "microsoft.graph.requestSignatureVerification"},
  "requiredResourceAccess": [{"@odata.type": "microsoft.graph.requiredResourceAccess"}],
  "servicePrincipalLockConfiguration": {"@odata.type": "microsoft.graph.servicePrincipalLockConfiguration"},
  "serviceManagementReference": "String",
  "signInAudience": "String",
  "spa": {"@odata.type": "microsoft.graph.spaApplication"},
  "tags": ["String"],
  "tokenEncryptionKeyId": "String",
  "verifiedPublisher": {"@odata.type": "microsoft.graph.verifiedPublisher"},
  "web": {"@odata.type": "microsoft.graph.webApplication"}
}
"""

# Resources

class permissionScopeResource(BaseModel):
    """
    permissionScope Schema: https://learn.microsoft.com/en-us/graph/api/resources/permissionscope?view=graph-rest-1.0
    """
    adminConsentDescription: Optional[str] = None
    adminConsentDisplayName: Optional[str] = None
    id: Optional[str] = None
    isEnabled: Optional[bool] = False
    type: Optional[str] = None
    userConsentDescription: Optional[str] = None
    userConsentDisplayName: Optional[str] = None
    value: Optional[str] = None

class preAuthorizedApplicationResource(BaseModel):
    """
    preAuthorizedApplication Schema: https://learn.microsoft.com/en-us/graph/api/resources/preauthorizedapplication?view=graph-rest-1.0
    """
    appId: Optional[str] = None
    delegatedPermissionIds: Optional[list] = []
    
# Applications
class apiApplicationResource(BaseModel):
    """
    apiApplication Schema: https://learn.microsoft.com/en-us/graph/api/resources/apiapplication?view=graph-rest-1.0
    """
    acceptMappedClaims: Optional[bool] = False
    knownClientApplications: Optional[list] = []
    oauth2PermissionScopes: Optional[List[permissionScopeResource]] = None
    preAuthorizedApplications: Optional[List[preAuthorizedApplicationResource]] = None
    requestedAccessTokenVersion: Optional[int] = 1

class appRoleResource(BaseModel):
    """
    appRole Schema: https://learn.microsoft.com/en-us/graph/api/resources/approle?view=graph-rest-1.0
    """
    allowedMemberTypes: Optional[list] = []
    description: Optional[str] = None
    displayName: Optional[str] = None
    id: Optional[str] = None
    isEnabled: Optional[bool] = False
    origin: Optional[str] = None
    value: Optional[str] = None

class certificationResource(BaseModel):
    """
    certification Schema: https://learn.microsoft.com/en-us/graph/api/resources/certification?view=graph-rest-1.0
    """
    certificationDetailsUrl: Optional[str] = None
    certificationExpirationDateTime: Optional[str] = None # DateTimeOffset : The timestamp when the current certification for the application expires. ISO 8601 format and is always in UTC time
    isCertifiedByMicrosoft: Optional[bool] = None
    isPublisherAttested: Optional[bool] = None
    lastCertificationDateTime: Optional[str] = None # DateTimeOffset : The timestamp when the certification for the application was most recently added or updated. ISO 8601 format and is always in UTC time

class informationalUrlResource(BaseModel):
    """
    informationalUrl Schema: https://learn.microsoft.com/en-us/graph/api/resources/informationalurl?view=graph-rest-1.0
    """
    logoUrl: Optional[str] = None
    marketingUrl: Optional[str] = None
    privacyStatementUrl: Optional[str] = None
    supportUrl: Optional[str] = None
    termsOfServiceUrl: Optional[str] = None

class keyCredentialResource(BaseModel):
    """
    keyCredential Schema: https://learn.microsoft.com/en-us/graph/api/resources/keycredential?view=graph-rest-1.0
    """
    customKeyIdentifier: Optional[str] = None
    displayName: Optional[str] = None
    endDateTime: Optional[str] = None # DateTimeOffset : The date and time at which the credential expires. The Timestamp type represents date and time information using ISO 8601 format and is always in UTC time. For example, midnight UTC on Jan 1, 2014 would look like this: '2014-01-01T00:00:00Z'
    key: Optional[str] = None # Required. Must be set to conitnue creating
    # keyId: Optional[str] = None # Not supported in Create Application
    # startDateTime: Optional[str] = None # Past dates throw an error...DateTimeOffset : The date and time at which the credential becomes valid. The Timestamp type represents date and time information using ISO 8601 format and is always in UTC time. For example, midnight UTC on Jan 1, 2014 would look like this: '2014-01-01T00:00:00Z'
    type: Optional[str] = None
    usage: Optional[str] = None

class optionalClaimResource(BaseModel):
    """
    optionalClaim Schema: https://learn.microsoft.com/en-us/graph/api/resources/optionalclaim?view=graph-rest-1.0
    """
    additionalProperties: Optional[List] = {}
    essential: Optional[bool] = False
    name: Optional[str] = None
    source: Optional[str] = None
    
class optionalClaimsResource(BaseModel):
    """
    optionalClaims Schema: https://learn.microsoft.com/en-us/graph/api/resources/optionalclaims?view=graph-rest-1.0
    """
    accessToken: Optional[List[optionalClaimResource]] = []
    idToken: Optional[List[optionalClaimResource]] = []
    saml2Token: Optional[List[optionalClaimResource]] = []

class parentalControlSettingsResource(BaseModel):
    """
    parentalControlSettings Schema: https://learn.microsoft.com/en-us/graph/api/resources/parentalcontrolsettings?view=graph-rest-1.0
    """
    countriesBlockedForMinors: Optional[list] = []
    legalAgeGroupRule: Optional[str] = None

class passwordCredentialResource(BaseModel):
    """
    passwordCredential Schema: https://learn.microsoft.com/en-us/graph/api/resources/passwordcredential?view=graph-rest-1.0
    Generate new passwords 
    """
    # customKeyIdentifier: Optional[str] = None
    displayName: Optional[str] = None
    endDateTime: Optional[str] = None # Expiratin will be set by policy. DateTimeOffset : The date and time at which the password expires. The Timestamp type represents date and time information using ISO 8601 format and is always in UTC time. For example, midnight UTC on Jan 1, 2014 would look like this: '2014-01-01T00:00:00Z'
    # hint: Optional[str] = None # Read only
    # keyId: Optional[str] = None # Not supported in Create Application
    # secretText: Optional[str] = None # read only. Use addPassword to set the password and receive the password in the response, shown only once.
    # startDateTime: Optional[str] = None # Past dates throw an error... DateTimeOffset : The date and time at which the password becomes valid. The Timestamp type represents date and time information using ISO 8601 format and is always in UTC time. For example, midnight UTC on Jan 1, 2014 would look like this: '2014-01-01T00:00:00Z'

class publicClientApplicationResource(BaseModel):
    """
    publicClientApplication Schema: https://learn.microsoft.com/en-us/graph/api/resources/publicclientapplication?view=graph-rest-1.0
    """
    redirectUris: Optional[list] = []
    
class requestSignatureVerificationResource(BaseModel):
    """
    requestSignatureVerification Schema: https://learn.microsoft.com/en-us/graph/api/resources/requestsignatureverification?view=graph-rest-1.0
    """
    allowedWeakAlgorithms: Optional[str] = None
    isSignedRequestRequired: Optional[bool] = False


class resourceAccessResource(BaseModel):
    """
    resourceAccess Schema: https://learn.microsoft.com/en-us/graph/api/resources/resourceaccess?view=graph-rest-1.0
    """
    id: Optional[str] = None
    type: Optional[str] = None
    
class requiredResourceAccessResource(BaseModel):
    """
    requiredResourceAccess Schema: https://learn.microsoft.com/en-us/graph/api/resources/requiredresourceaccess?view=graph-rest-1.0
    """
    resourceAccess: Optional[List[resourceAccessResource]] = None
    resourceAppId: Optional[str] = None


class servicePrincipalLockConfigurationResource(BaseModel):
    """
    servicePrincipalLockConfiguration Schema: https://learn.microsoft.com/en-us/graph/api/resources/serviceprincipallockconfiguration?view=graph-rest-1.0
    """
    isEnabled: Optional[bool] = None
    allProperties: Optional[bool] = None
    credentialsWithUsageVerify: Optional[bool] = None
    credentialsWithUsageSign: Optional[bool] = None
    tokenEncryptionKeyId: Optional[bool] = None

class spaApplicationResource(BaseModel):
    """
    spaApplication Schema: https://learn.microsoft.com/en-us/graph/api/resources/spaapplication?view=graph-rest-1.0
    """
    redirectUris: Optional[list] = []

class verifiedPublisherResource(BaseModel):
    """
    verifiedPublisher Schema: https://learn.microsoft.com/en-us/graph/api/resources/verifiedpublisher?view=graph-rest-1.0
    """
    addedDateTime: Optional[str] = None # DateTimeOffset : The timestamp when the verified publisher was added. ISO 8601 format and is always in UTC time
    displayName: Optional[str] = None
    verifiedPublisherId: Optional[str] = None

class implicitGrantSettingsResource(BaseModel):
    """
    implicitGrantSettings Schema: https://learn.microsoft.com/en-us/graph/api/resources/implicitgrantsettings?view=graph-rest-1.0
    """
    enableAccessTokenIssuance: Optional[bool] = False
    enableIdTokenIssuance: Optional[bool] = False

class webApplicationResource(BaseModel):
    """
    webApplication Schema: https://learn.microsoft.com/en-us/graph/api/resources/webapplication?view=graph-rest-1.0
    """
    homePageUrl: Optional[str] = None
    implicitGrantSettings: Optional[implicitGrantSettingsResource] = None
    logoutUrl: Optional[str] = None
    redirectUris: Optional[list] = None

class addIn(BaseModel):
    """
    https://learn.microsoft.com/en-us/graph/api/resources/addin?view=graph-rest-1.0
    """
    id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    type: Optional[str] = None
    
# Application Models

class ApplicationModel(BaseModel):
    """
    Application Schema: https://learn.microsoft.com/en-us/graph/api/resources/application?view=graph-rest-1.0#properties
    """
    model_config = {
        # 'use_enum_values': True,
    }
    
    original_ref: Optional[str] = None
    
    addIns: Optional[List[addIn]] = None
    api: Optional[apiApplicationResource] = None
    appId: Optional[str] = None # read-only
    applicationTemplateId: Optional[str] = None
    appRoles: Optional[List[appRoleResource]] = None
    # certification: Optional[certificationResource] = None # Compliance feature with MS365. Not needed.
    createdDateTime: Optional[str] = None # ISO 8601 format and is always in UTC time
    deletedDateTime: Optional[str] = None # ISO 8601 format and is always in UTC time
    description: Optional[str] = None
    disabledByMicrosoftStatus: Optional[str] = None
    displayName: Optional[str]
    groupMembershipClaims: Optional[str] = None
    id: Optional[str] = None # UUID
    identifierUris: Optional[list] = []
    info: Optional[informationalUrlResource] = None
    isDeviceOnlyAuthSupported: Optional[bool] = False
    isFallbackPublicClient: Optional[bool] = False
    keyCredentials: Optional[List[keyCredentialResource]] = None # Certificates will need to be created separately in Azure
    logo: Optional[str] = None
    notes: Optional[str] = None
    oauth2RequiredPostResponse: Optional[bool] = False
    optionalClaims: Optional[optionalClaimsResource] = None
    parentalControlSettings: Optional[parentalControlSettingsResource] = None
    passwordCredentials: Optional[List[passwordCredentialResource]] = None 
    publicClient: Optional[publicClientApplicationResource] = {}
    publisherDomain: Optional[str] = None # Currently, you can't use REST API or PowerShell to programmatically set a publisher domain. https://learn.microsoft.com/en-us/entra/identity-platform/howto-configure-publisher-domain
    requestSignatureVerification: Optional[requestSignatureVerificationResource] = None
    requiredResourceAccess: Optional[List[requiredResourceAccessResource]] = None
    samlMetadataUrl: Optional[str] = None
    servicePrincipalLockConfiguration: Optional[servicePrincipalLockConfigurationResource] = None
    serviceManagementReference: Optional[str] = None
    signInAudience: Optional[str] = None
    spa: Optional[spaApplicationResource] = None
    tags: Optional[list] = None
    tokenEncryptionKeyId: Optional[str] = None
    uniqueName: Optional[str] = None
    verifiedPublisher: Optional[verifiedPublisherResource] = None
    web: Optional[webApplicationResource] = None
    
    def post_model(self, exclude:list=[]):
        # Create new app
        return self.model_dump(exclude=['original_ref','id','displayName','appId','applicationTemplateId','createdDateTime','deletedDateTime','publisherDomain','uniqueName'] + exclude, exclude_unset=True, exclude_none=True)

