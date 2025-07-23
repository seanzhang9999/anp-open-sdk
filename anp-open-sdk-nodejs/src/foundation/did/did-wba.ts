/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as crypto from 'crypto';
import axios from 'axios';
import { 
  DIDDocument, 
  KeyPair, 
  AuthData, 
  AuthHeaderParts, 
  SignCallback,
  VerifyResult,
  JWK,
  VerificationMethod 
} from './types';
import { createVerificationMethod } from './verification-methods';

// JSON Canonicalization Scheme implementation (simplified)
function canonicalizeJSON(obj: any): string {
  if (obj === null) return 'null';
  if (typeof obj === 'boolean' || typeof obj === 'number') return String(obj);
  if (typeof obj === 'string') return JSON.stringify(obj);
  
  if (Array.isArray(obj)) {
    const items = obj.map(item => canonicalizeJSON(item));
    return '[' + items.join(',') + ']';
  }
  
  if (typeof obj === 'object') {
    const keys = Object.keys(obj).sort();
    const pairs = keys.map(key => JSON.stringify(key) + ':' + canonicalizeJSON(obj[key]));
    return '{' + pairs.join(',') + '}';
  }
  
  throw new Error(`Cannot canonicalize value of type ${typeof obj}`);
}

function isIpAddress(hostname: string): boolean {
  // IPv4 pattern
  const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
  // IPv6 pattern (simplified)
  const ipv6Pattern = /^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$/;
  
  return ipv4Pattern.test(hostname) || ipv6Pattern.test(hostname);
}

function encodeBase64Url(data: Uint8Array): string {
  return Buffer.from(data).toString('base64url');
}

function publicKeyToJwk(keyObject: crypto.KeyObject, curve: string): JWK {
  const jwk = keyObject.export({ format: 'jwk' }) as any;
  
  if (curve === 'secp256k1') {
    // For secp256k1, we need to generate kid from compressed public key
    const compressedKey = crypto.publicEncrypt({
      key: keyObject,
      padding: crypto.constants.RSA_NO_PADDING
    }, Buffer.alloc(0));
    
    const kid = crypto.createHash('sha256').update(compressedKey).digest();
    jwk.kid = encodeBase64Url(kid);
  }
  
  return jwk;
}

export class DIDWbaAuth {
  /**
   * Create DID WBA document
   */
  public static async createDidWbaDocument(
    hostname: string,
    port?: number,
    pathSegments?: string[],
    agentDescriptionUrl?: string,
    curve: string = 'secp256k1'
  ): Promise<{ document: DIDDocument; keys: Record<string, KeyPair> }> {
    
    // Generate key pair
    let keyPair: crypto.KeyPairSyncResult<string, string>;
    
    if (curve === 'secp256k1') {
      keyPair = crypto.generateKeyPairSync('ec', {
        namedCurve: 'secp256k1',
        publicKeyEncoding: { type: 'spki', format: 'pem' },
        privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
      });
    } else if (curve === 'Ed25519') {
      keyPair = crypto.generateKeyPairSync('ed25519', {
        publicKeyEncoding: { type: 'spki', format: 'pem' },
        privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
      });
    } else {
      throw new Error(`Unsupported curve: ${curve}`);
    }

    // Convert to crypto.KeyObject for JWK generation
    const publicKeyObj = crypto.createPublicKey(keyPair.publicKey);
    const privateKeyObj = crypto.createPrivateKey(keyPair.privateKey);

    // Generate DID
    const portSuffix = port ? `_${port}` : '';
    const pathSuffix = pathSegments ? `_${pathSegments.join('_')}` : '';
    const did = `did:wba:${hostname}${portSuffix}${pathSuffix}`;

    // Create JWK
    const jwk = publicKeyToJwk(publicKeyObj, curve);

    // Create verification method
    const verificationMethod: VerificationMethod = {
      id: `${did}#key-1`,
      type: curve === 'secp256k1' ? 'EcdsaSecp256k1VerificationKey2019' : 'Ed25519VerificationKey2018',
      controller: did,
      publicKeyJwk: jwk
    };

    // Create DID document
    const document: DIDDocument = {
      '@context': [
        'https://www.w3.org/ns/did/v1',
        'https://w3id.org/security/suites/jws-2020/v1',
        curve === 'secp256k1' 
          ? 'https://w3id.org/security/suites/secp256k1-2019/v1'
          : 'https://w3id.org/security/suites/ed25519-2018/v1'
      ],
      id: did,
      verificationMethod: [verificationMethod],
      authentication: [verificationMethod.id]
    };

    // Add service if agent description URL is provided
    if (agentDescriptionUrl) {
      document.service = [{
        id: `${did}#agent-description`,
        type: 'AgentDescription',
        serviceEndpoint: agentDescriptionUrl
      }];
    }

    // Extract key bytes
    const privateKeyBytes = new Uint8Array(Buffer.from(keyPair.privateKey, 'utf8'));
    const publicKeyBytes = new Uint8Array(Buffer.from(keyPair.publicKey, 'utf8'));

    return {
      document,
      keys: {
        'key-1': {
          privateKey: privateKeyBytes,
          publicKey: publicKeyBytes
        }
      }
    };
  }

  /**
   * Resolve DID WBA document
   */
  public static async resolveDidWbaDocument(did: string): Promise<DIDDocument> {
    // Extract hostname and port from DID
    const match = did.match(/^did:wba:(.+?)(?:_(\d+))?(?:_(.+))?$/);
    if (!match) {
      throw new Error(`Invalid DID format: ${did}`);
    }

    const [, hostname, portStr, pathSegments] = match;
    const port = portStr ? parseInt(portStr, 10) : (isIpAddress(hostname) ? 9527 : 443);
    const protocol = isIpAddress(hostname) || port !== 443 ? 'http' : 'https';
    
    let url: string;
    if (pathSegments) {
      const segments = pathSegments.split('_');
      url = `${protocol}://${hostname}:${port}/${segments.join('/')}/did.json`;
    } else {
      url = `${protocol}://${hostname}:${port}/did.json`;
    }

    try {
      const response = await axios.get(url, { timeout: 10000 });
      return response.data as DIDDocument;
    } catch (error) {
      throw new Error(`Failed to resolve DID document: ${error}`);
    }
  }

  /**
   * Generate authentication header
   */
  public static async generateAuthHeader(
    didDocument: DIDDocument,
    serviceDomain: string,
    signCallback: SignCallback,
    respDid?: string
  ): Promise<string> {
    
    // Generate nonce and timestamp
    const nonce = crypto.randomBytes(16).toString('hex');
    const timestamp = new Date().toISOString();

    // Create auth data
    const authData: AuthData = {
      nonce,
      timestamp,
      service: serviceDomain,
      did: didDocument.id
    };

    if (respDid) {
      authData.resp_did = respDid;
    }

    // Canonicalize and hash
    const canonical = canonicalizeJSON(authData);
    const content = new Uint8Array(Buffer.from(canonical, 'utf8'));
    const hash = crypto.createHash('sha256').update(content).digest();

    // Sign
    const signature = await signCallback(hash);
    const signatureB64 = encodeBase64Url(signature);

    // Find verification method
    const verificationMethod = didDocument.verificationMethod[0];
    if (!verificationMethod) {
      throw new Error('No verification method found in DID document');
    }

    // Build header
    let headerParts = [
      `did="${didDocument.id}"`,
      `nonce="${nonce}"`,
      `timestamp="${timestamp}"`,
      `verification_method="${verificationMethod.id.split('#')[1]}"`,
      `signature="${signatureB64}"`
    ];

    if (respDid) {
      headerParts.splice(3, 0, `resp_did="${respDid}"`);
    }

    return `DIDWba ${headerParts.join(', ')}`;
  }

  /**
   * Verify authentication header signature
   */
  public static async verifyAuthHeaderSignature(
    authHeader: string,
    didDocument: DIDDocument,
    serviceDomain: string
  ): Promise<VerifyResult> {
    
    try {
      // Parse header
      const parts = this.extractAuthHeaderParts(authHeader);
      
      // Reconstruct auth data
      const authData: AuthData = {
        nonce: parts.nonce,
        timestamp: parts.timestamp,
        service: serviceDomain,
        did: parts.did
      };

      if (parts.respDid) {
        authData.resp_did = parts.respDid;
      }

      // Find verification method
      const vmId = `${parts.did}#${parts.verificationMethod}`;
      const verificationMethod = didDocument.verificationMethod.find(vm => vm.id === vmId);
      
      if (!verificationMethod) {
        return {
          valid: false,
          message: `Verification method not found: ${vmId}`
        };
      }

      // Canonicalize and hash
      const canonical = canonicalizeJSON(authData);
      const content = new Uint8Array(Buffer.from(canonical, 'utf8'));
      const hash = crypto.createHash('sha256').update(content).digest();

      // Verify signature
      const verifier = createVerificationMethod(verificationMethod);
      const valid = await verifier.verifySignature(hash, parts.signature);

      return {
        valid,
        message: valid ? 'Signature verification successful' : 'Signature verification failed',
        payload: valid ? authData : undefined
      };

    } catch (error) {
      return {
        valid: false,
        message: `Verification error: ${error}`
      };
    }
  }

  /**
   * Extract auth header parts
   */
  public static extractAuthHeaderParts(authHeader: string): AuthHeaderParts {
    // Remove "DIDWba " prefix
    const headerContent = authHeader.replace(/^DIDWba\s+/, '');
    
    // Parse key=value pairs
    const parts: Record<string, string> = {};
    const regex = /(\w+)="([^"]+)"/g;
    let match;
    
    while ((match = regex.exec(headerContent)) !== null) {
      parts[match[1]] = match[2];
    }

    // Validate required fields
    const required = ['did', 'nonce', 'timestamp', 'verification_method', 'signature'];
    for (const field of required) {
      if (!parts[field]) {
        throw new Error(`Missing required field: ${field}`);
      }
    }

    return {
      did: parts.did,
      nonce: parts.nonce,
      timestamp: parts.timestamp,
      verificationMethod: parts.verification_method,
      signature: parts.signature,
      respDid: parts.resp_did
    };
  }
}