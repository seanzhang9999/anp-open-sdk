/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

// Core interfaces based on agent-connect implementation

export interface JWK {
  kty: string;
  crv: string;
  x?: string;  // for EC keys
  y?: string;  // for EC keys  
  kid?: string;
}

export interface VerificationMethod {
  id: string;
  type: string;
  controller: string;
  publicKeyJwk?: JWK;
  publicKeyMultibase?: string;
}

export interface Service {
  id: string;
  type: string;
  serviceEndpoint: string;
}

export interface DIDDocument {
  '@context': string[];
  id: string;
  verificationMethod: VerificationMethod[];
  authentication: string[];
  service?: Service[];
}

export interface KeyPair {
  privateKey: Uint8Array;
  publicKey: Uint8Array;
}

export interface AuthData {
  nonce: string;
  timestamp: string;
  service?: string;      // for single-way authentication
  anp_service?: string;  // for two-way authentication
  did: string;
  resp_did?: string;     // for two-way authentication
}

export interface AuthHeaderParts {
  did: string;
  nonce: string;
  timestamp: string;
  verificationMethod: string;
  signature: string;
  respDid?: string;
}

export interface SignCallback {
  (data: Uint8Array): Promise<Uint8Array>;
}

export interface VerifyResult {
  valid: boolean;
  message: string;
  payload?: AuthData;
}