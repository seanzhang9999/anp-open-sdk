/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as crypto from 'crypto';
import { VerificationMethod } from './types';

export abstract class VerificationMethodBase {
  public abstract verifySignature(content: Uint8Array, signature: string): Promise<boolean>;
  
  public static encodeSignature(signatureBytes: Uint8Array): string {
    // Convert DER to R|S format first, then base64url encode
    const rsBytes = this.derToRS(signatureBytes);
    return Buffer.from(rsBytes).toString('base64url');
  }

  public static decodeSignature(signature: string): Uint8Array {
    // Handle base64url padding and decode
    const padded = signature + '='.repeat((4 - signature.length % 4) % 4);
    return new Uint8Array(Buffer.from(padded, 'base64url'));
  }

  private static derToRS(derSignature: Uint8Array): Uint8Array {
    // Convert DER format to R|S format (64 bytes for secp256k1)
    if (derSignature[0] !== 0x30) {
      throw new Error('Invalid DER signature format');
    }

    let offset = 2; // Skip 0x30 and total length
    
    // Parse R
    if (derSignature[offset] !== 0x02) {
      throw new Error('Invalid DER signature: R component missing');
    }
    const rLength = derSignature[offset + 1];
    offset += 2;
    
    let r = derSignature.slice(offset, offset + rLength);
    offset += rLength;
    
    // Parse S
    if (derSignature[offset] !== 0x02) {
      throw new Error('Invalid DER signature: S component missing');
    }
    const sLength = derSignature[offset + 1];
    offset += 2;
    
    let s = derSignature.slice(offset, offset + sLength);
    
    // Remove leading zeros and pad to 32 bytes
    r = this.padTo32Bytes(this.removeLeadingZeros(r));
    s = this.padTo32Bytes(this.removeLeadingZeros(s));
    
    // Combine R and S
    const result = new Uint8Array(64);
    result.set(r, 0);
    result.set(s, 32);
    
    return result;
  }

  private static removeLeadingZeros(bytes: Uint8Array): Uint8Array {
    let start = 0;
    while (start < bytes.length && bytes[start] === 0) {
      start++;
    }
    return bytes.slice(start);
  }

  private static padTo32Bytes(bytes: Uint8Array): Uint8Array {
    if (bytes.length > 32) {
      throw new Error('Component too long for secp256k1');
    }
    const padded = new Uint8Array(32);
    padded.set(bytes, 32 - bytes.length);
    return padded;
  }
}

export class EcdsaSecp256k1VerificationKey2019 extends VerificationMethodBase {
  private publicKey: crypto.KeyObject;

  constructor(jwk: any) {
    super();
    
    // Convert JWK to Node.js KeyObject
    this.publicKey = crypto.createPublicKey({
      key: {
        kty: jwk.kty,
        crv: jwk.crv,
        x: jwk.x,
        y: jwk.y
      },
      format: 'jwk'
    });
  }

  public async verifySignature(content: Uint8Array, signature: string): Promise<boolean> {
    try {
      // Decode base64url signature (should be R|S format, 64 bytes)
      const signatureBytes = VerificationMethodBase.decodeSignature(signature);
      
      if (signatureBytes.length !== 64) {
        console.warn(`Expected 64-byte R|S signature, got ${signatureBytes.length} bytes`);
        return false;
      }
      
      // Convert R|S format to DER format for Node.js crypto verification
      const r = signatureBytes.slice(0, 32);
      const s = signatureBytes.slice(32);
      const derSignature = this.encodeDERSignature(r, s);
      
      // Verify signature using Node.js crypto
      const verify = crypto.createVerify('SHA256');
      verify.update(content);
      
      return verify.verify(this.publicKey, derSignature);
    } catch (error) {
      console.warn('ECDSA signature verification failed:', error);
      return false;
    }
  }

  private encodeDERSignature(r: Uint8Array, s: Uint8Array): Buffer {
    // DER encoding for ECDSA signature
    // Format: 0x30 [total-length] 0x02 [R-length] [R] 0x02 [S-length] [S]
    
    // Remove leading zeros but ensure we don't have negative numbers
    const rTrimmed = this.trimLeadingZeros(r);
    const sTrimmed = this.trimLeadingZeros(s);
    
    // Add leading zero if the high bit is set (to avoid negative interpretation)
    const rFinal = (rTrimmed[0] & 0x80) ? Buffer.concat([Buffer.from([0x00]), rTrimmed]) : rTrimmed;
    const sFinal = (sTrimmed[0] & 0x80) ? Buffer.concat([Buffer.from([0x00]), sTrimmed]) : sTrimmed;
    
    const rWithHeader = Buffer.concat([Buffer.from([0x02, rFinal.length]), rFinal]);
    const sWithHeader = Buffer.concat([Buffer.from([0x02, sFinal.length]), sFinal]);
    const totalLength = rWithHeader.length + sWithHeader.length;
    
    return Buffer.concat([
      Buffer.from([0x30, totalLength]),
      rWithHeader,
      sWithHeader
    ]);
  }

  private trimLeadingZeros(bytes: Uint8Array): Buffer {
    let start = 0;
    while (start < bytes.length - 1 && bytes[start] === 0) {
      start++;
    }
    return Buffer.from(bytes.slice(start));
  }

  public static fromVerificationMethod(vm: VerificationMethod): EcdsaSecp256k1VerificationKey2019 {
    if (!vm.publicKeyJwk) {
      throw new Error('Missing publicKeyJwk in verification method');
    }
    return new EcdsaSecp256k1VerificationKey2019(vm.publicKeyJwk);
  }
}

export class Ed25519VerificationKey2018 extends VerificationMethodBase {
  private publicKey: crypto.KeyObject;

  constructor(jwk: any) {
    super();
    
    this.publicKey = crypto.createPublicKey({
      key: {
        kty: jwk.kty,
        crv: jwk.crv,
        x: jwk.x
      },
      format: 'jwk'
    });
  }

  public async verifySignature(content: Uint8Array, signature: string): Promise<boolean> {
    try {
      const signatureBytes = VerificationMethodBase.decodeSignature(signature);
      
      // Ed25519 verification
      const verify = crypto.createVerify('Ed25519');
      verify.update(content);
      
      return verify.verify(this.publicKey, signatureBytes);
    } catch (error) {
      console.warn('Ed25519 signature verification failed:', error);
      return false;
    }
  }

  public static fromVerificationMethod(vm: VerificationMethod): Ed25519VerificationKey2018 {
    if (!vm.publicKeyJwk) {
      throw new Error('Missing publicKeyJwk in verification method');
    }
    return new Ed25519VerificationKey2018(vm.publicKeyJwk);
  }
}

// Supported curve mapping
export const CURVE_MAPPING = {
  'secp256k1': 'secp256k1',
  'P-256': 'prime256v1',
  'P-384': 'secp384r1', 
  'P-521': 'secp521r1'
};

// Factory function to create verification method instance
export function createVerificationMethod(vm: VerificationMethod): VerificationMethodBase {
  switch (vm.type) {
    case 'EcdsaSecp256k1VerificationKey2019':
      return EcdsaSecp256k1VerificationKey2019.fromVerificationMethod(vm);
    case 'Ed25519VerificationKey2018':
      return Ed25519VerificationKey2018.fromVerificationMethod(vm);
    default:
      throw new Error(`Unsupported verification method type: ${vm.type}`);
  }
}