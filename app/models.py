from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None


class MetricEntryCreate(BaseModel):
    date: str
    bloodPressure: Optional[str] = None
    bloodSugar: Optional[float] = None
    weight: Optional[float] = None
    heartRate: Optional[float] = None
    oxygenSaturation: Optional[float] = None
    temperature: Optional[float] = None
    notes: Optional[str] = None


class FamilyMemberCreate(BaseModel):
    fullName: str
    relationship: str
    age: int
    gender: str
    bloodGroup: str
    phone: str = ""
    email: str = ""
    emergencyContact: str = ""
    conditions: list[str] = []
    allergies: list[str] = []
    medications: list[str] = []
    healthNotes: str = ""
    wellbeingNotes: str = ""
    wellbeingStatus: str = "Good"
    photo: Optional[str] = None


class ReportCreate(BaseModel):
    ownerType: str
    ownerId: Optional[str] = None
    reportName: str
    reportCategory: str
    reportDate: str
    healthcareFacility: str
    notes: str = ""
    fileName: str
    fileType: str
    fileSize: int
    fileUrl: str = ""
    uploadedDate: str
    createdBy: str


class DeviceCreate(BaseModel):
    name: str
    icon: str
    status: str
    lastSync: str
    dataTypes: str
    accent: str


class SettingsUpdate(BaseModel):
    push: Optional[bool] = None
    email: Optional[bool] = None
    sms: Optional[bool] = None
    glucoseHigh: Optional[float] = None
    sleepLow: Optional[float] = None
    hrHigh: Optional[float] = None
    hipaaAudit: Optional[bool] = None
    encryption: Optional[bool] = None
    gdprExport: Optional[bool] = None
    autoPurge: Optional[bool] = None


class NoteCreate(BaseModel):
    note: str
    createdBy: Optional[str] = "Unknown"


class AdminProviderCreate(BaseModel):
    displayName: str
    description: str = ""
    providerType: str
    fhirEndpoint: str
    apiVersion: str = "R4"
    webhookUrl: Optional[str] = None
    environment: str = "sandbox"
    authType: str
    clientId: Optional[str] = None
    tokenUrl: Optional[str] = None
    authorizationUrl: Optional[str] = None
    scopes: Optional[str] = None
    apiKey: Optional[str] = None
    apiKeyHeader: Optional[str] = "X-API-Key"
    ipWhitelist: Optional[str] = None
    supportedDataTypes: list[str] = []
    templateId: Optional[str] = None
    supportsOtp: bool = True
    supportsOAuth: bool = False
    otpContactMethods: list[str] = []
    notes: Optional[str] = None


class IntegrationCreate(BaseModel):
    name: str
    provider: str
    environment: str = "sandbox"
    baseUrl: str
    apiVersion: str
    webhookUrl: Optional[str] = None
    authType: str
    dataTypes: list[str] = []
    syncFrequency: str = "scheduled"
    cronExpression: Optional[str] = None
    triggers: list[str] = []


class OtpRequest(BaseModel):
    contact: str
    channel: str
    providerId: str
    subjectId: str


class OtpVerify(BaseModel):
    sessionId: str
    otp: str
    contact: str


class ConnectProviderRequest(BaseModel):
    subjectId: str
    subjectName: str
    subjectType: str
    providerId: str
    dataTypes: list[str]
    sessionToken: str
    consentGiven: bool
    consentSignature: str = ""


class StatusUpdate(BaseModel):
    status: str


class CertUpload(BaseModel):
    providerId: str
    keyType: str
    fileBase64: str
    fileMimeType: str
    expiresAt: Optional[str] = None
    notes: Optional[str] = None
    actorUserId: str
