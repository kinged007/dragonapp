from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta


class addIn(BaseModel):
    """
    https://learn.microsoft.com/en-us/graph/api/resources/addin?view=graph-rest-1.0
    """
    id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    type: Optional[str] = None
    
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

class informationalUrlResource(BaseModel):
    """
    informationalUrlResource Schema: https://learn.microsoft.com/en-us/graph/api/resources/informationalurl?view=graph-rest-1.0
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
    # customKeyIdentifier: Optional[str] = None 
    displayName: Optional[str] = None
    endDateTime: Optional[str] = None  # DateTimeOffset : The timestamp when the current certification for the application expires. ISO 8601 format and is always in UTC time
    # key: Optional[str] = None
    # keyId: Optional[str] = None
    # startDateTime: Optional[str] = None
    type: Optional[str] = None
    usage: Optional[str] = None

class oauth2PermissionScopeResource(BaseModel):
    """
    oauth2PermissionScope Schema: https://learn.microsoft.com/en-us/graph/api/resources/oauth2permissionscope?view=graph-rest-1.0
    """
    adminConsentDescription: Optional[str] = None
    adminConsentDisplayName: Optional[str] = None
    # id: Optional[str] = None
    isEnabled: Optional[bool] = False
    type: Optional[str] = None
    userConsentDescription: Optional[str] = None
    userConsentDisplayName: Optional[str] = None
    value: Optional[str] = None

class passwordCredentialResource(BaseModel):
    """
    passwordCredential Schema: https://learn.microsoft.com/en-us/graph/api/resources/passwordcredential?view=graph-rest-1.0
    NOTE: 
    Using POST or PATCH to set the passwordCredential property is not supported. Use the following addPassword and removePassword methods to update the password or secret for an application or a servicePrincipal:


    """
    # customKeyIdentifier: Optional[str] = None
    displayName: Optional[str] = None
    endDateTime: Optional[str] = None
    # hint: Optional[str] = None
    # keyId: Optional[str] = None
    # secretText: Optional[str] = None
    # startDateTime: Optional[str] = None

class resourceSpecificApplicationPermission(BaseModel):
    """
    https://learn.microsoft.com/en-us/graph/api/resources/resourcespecificpermission?view=graph-rest-1.0
    """
    description: Optional[str] = None
    displayName: Optional[str] = None
    id: Optional[str] = None
    isEnabled: Optional[bool] = False
    value: Optional[str] = None

class samlSingleSignOnSettingsResource(BaseModel):
    """
    https://learn.microsoft.com/en-us/graph/api/resources/samlsinglesignonsettings?view=graph-rest-1.0
    """
    relayState: Optional[str] = None
    
class verifiedPublisherResource(BaseModel):
    """
    https://learn.microsoft.com/en-us/graph/api/resources/verifiedpublisher?view=graph-rest-1.0
    """
    verifiedPublisherId: Optional[str] = None
    addedDateTime: Optional[str] = None
    displayName: Optional[str] = None    
    

class ServicePrincipalModel(BaseModel):
    """
    Application Schema: https://learn.microsoft.com/en-us/graph/api/resources/application?view=graph-rest-1.0#properties
    """
    model_config = {
        # 'use_enum_values': True,
    }

    # certification: Optional[certificationResource] = None # Compliance feature with MS365. Not needed.
    accountEnabled: Optional[bool] = True
    addIns: Optional[List[addIn]] = None
    alternativeNames: Optional[List[str]] = None
    appDescription: Optional[str] = None
    appDisplayName: Optional[str] = None
    appId: Optional[str] = None # read-only # IMPORTANT: SHould be the AppId of the NEW application, not the old one. We need to use a previous Application migration job ot get the new AppId
    applicationTemplateId: Optional[str] = None
    appOwnerOrganizationId: Optional[str] = None
    appRoleAssignmentRequired: Optional[bool] = False
    # appRoles: Optional[List[appRoleResource]] = None # Potentially not utilized. TODO check if migrated apps are using this or not, or additional roles apart from standard.
    customSecurityAttributes:Optional[str] = None
    deletedDateTime: Optional[str] = None # ISO 8601 format and is always in UTC time
    description: Optional[str] = None
    disabledByMicrosoftStatus: Optional[str] = None
    displayName: Optional[str] = None
    homepage: Optional[str] = None
    id: Optional[str] = None # UUID
    info: Optional[informationalUrlResource] = None
    keyCredentials: Optional[List[keyCredentialResource]] = None # Certificates will need to be created separately in Azure
    loginUrl: Optional[str] = None
    logoutUrl: Optional[str] = None
    notes: Optional[str] = None
    notificationEmailAddresses: Optional[List[str]] = None
    oauth2PermissionScopes: Optional[List[oauth2PermissionScopeResource]] = None # read-only
    passwordCredentials: Optional[List[passwordCredentialResource]] = None
    preferredSingleSignOnMode: Optional[str] = None
    preferredTokenSigningKeyThumbprint: Optional[str] = None
    replyUrls: Optional[List[str]] = None
    resourceSpecificApplicationPermissions: Optional[List[resourceSpecificApplicationPermission]] = None
    samlSingleSignOnSettings: Optional[samlSingleSignOnSettingsResource] = None
    servicePrincipalNames: Optional[List[str]] = None
    servicePrincipalType: Optional[str] = None
    signInAudience: Optional[str] = None
    tags: Optional[List[str]] = None
    tokenEncryptionKeyId: Optional[str] = None
    verifiedPublisher: Optional[verifiedPublisherResource] = None
    
    

    def post_model(self):
        # Create new app
        return self.model_dump(exclude=['id','applicationTemplateId','appDisplayName','deletedDateTime',
            'resourceSpecificApplicationPermissions','signInAudience','appOwnerOrganizationId','info',
            'displayName'
        ],exclude_unset=True,  exclude_none=True)
