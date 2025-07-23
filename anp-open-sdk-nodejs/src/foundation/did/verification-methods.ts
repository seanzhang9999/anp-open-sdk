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
    return Buffer.from(signatureBytes)
      .toString('base64url');
  }

  public static decodeSignature(signature: string): Uint8Array {
    // Handle base64url padding
    const padded = signature + '='.repeat((4 - signature.length % 4) % 4);
    return new Uint8Array(Buffer.from(padded, 'base64url'));
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
      // Decode base64url signature
      const signatureBytes = VerificationMethodBase.decodeSignature(signature);
      
      // Convert R|S format to DER format for secp256k1
      const rLength = signatureBytes.length / 2;
      const r = signatureBytes.slice(0, rLength);
      const s = signatureBytes.slice(rLength);
      
      // Create DER encoded signature
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
    // Simple DER encoding for ECDSA signature
    // Format: 0x30 [total-length] 0x02 [R-length] [R] 0x02 [S-length] [S]
    
    const rWithHeader = Buffer.concat([Buffer.from([0x02, r.length]), r]);
    const sWithHeader = Buffer.concat([Buffer.from([0x02, s.length]), s]);
    const totalLength = rWithHeader.length + sWithHeader.length;
    
    return Buffer.concat([
      Buffer.from([0x30, totalLength]),
      rWithHeader,
      sWithHeader
    ]);
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