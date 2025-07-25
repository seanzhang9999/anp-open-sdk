/**
 * Copyright 2024 ANP Open SDK Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 */

import * as crypto from 'crypto';
import { DIDWbaAuth } from '../../src/foundation/did/did-wba';
import { DIDDocument, SignCallback, AuthData } from '../../src/foundation/did/types';

describe('DIDWbaAuth - Two-Way Authentication', () => {
  let testDidDocument: DIDDocument;
  let testPrivateKey: crypto.KeyObject;
  let testSignCallback: SignCallback;

  beforeAll(async () => {
    // Generate test key pair
    const keyPair = crypto.generateKeyPairSync('ec', {
      namedCurve: 'secp256k1',
      publicKeyEncoding: { type: 'spki', format: 'pem' },
      privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
    });

    testPrivateKey = crypto.createPrivateKey(keyPair.privateKey);
    const publicKeyObj = crypto.createPublicKey(keyPair.publicKey);

    // Create test DID document
    const did = 'did:wba:test.example.com';
    testDidDocument = {
      '@context': [
        'https://www.w3.org/ns/did/v1',
        'https://w3id.org/security/suites/jws-2020/v1',
        'https://w3id.org/security/suites/secp256k1-2019/v1'
      ],
      id: did,
      verificationMethod: [{
        id: `${did}#key-1`,
        type: 'EcdsaSecp256k1VerificationKey2019',
        controller: did,
        publicKeyJwk: publicKeyObj.export({ format: 'jwk' }) as any
      }],
      authentication: [`${did}#key-1`]
    };

    // Create test sign callback
    testSignCallback = async (data: Uint8Array): Promise<Uint8Array> => {
      const signature = crypto.sign('sha256', data, testPrivateKey);
      return new Uint8Array(signature);
    };
  });

  describe('generateAuthHeaderTwoWay', () => {
    it('should generate valid two-way authentication header', async () => {
      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';

      const authHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      expect(authHeader).toMatch(/^DIDWba /);
      expect(authHeader).toContain(`did="${testDidDocument.id}"`);
      expect(authHeader).toContain(`resp_did="${respDid}"`);
      expect(authHeader).toContain('nonce=');
      expect(authHeader).toContain('timestamp=');
      expect(authHeader).toContain('verification_method="key-1"');
      expect(authHeader).toContain('signature=');
    });

    it('should include resp_did in the correct position', async () => {
      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';

      const authHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      // resp_did should appear before verification_method
      const respDidIndex = authHeader.indexOf('resp_did=');
      const verificationMethodIndex = authHeader.indexOf('verification_method=');
      
      expect(respDidIndex).toBeGreaterThan(-1);
      expect(verificationMethodIndex).toBeGreaterThan(-1);
      expect(respDidIndex).toBeLessThan(verificationMethodIndex);
    });

    it('should throw error when no verification method found', async () => {
      const invalidDidDocument = {
        ...testDidDocument,
        verificationMethod: []
      };

      await expect(
        DIDWbaAuth.generateAuthHeaderTwoWay(
          invalidDidDocument,
          'did:wba:target.example.com',
          'test.service.com',
          testSignCallback
        )
      ).rejects.toThrow('No verification method found in DID document');
    });
  });

  describe('extractAuthHeaderPartsTwoWay', () => {
    it('should extract all parts from two-way auth header', async () => {
      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';

      const authHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      const parts = DIDWbaAuth.extractAuthHeaderPartsTwoWay(authHeader);

      expect(parts.did).toBe(testDidDocument.id);
      expect(parts.respDid).toBe(respDid);
      expect(parts.nonce).toMatch(/^[a-f0-9]{32}$/);
      expect(parts.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
      expect(parts.verificationMethod).toBe('key-1');
      expect(parts.signature).toMatch(/^[A-Za-z0-9_-]+$/);
    });

    it('should throw error when resp_did is missing', () => {
      const headerWithoutRespDid = 'DIDWba did="did:wba:test.example.com", nonce="abc123", timestamp="2024-01-01T00:00:00.000Z", verification_method="key-1", signature="test"';

      expect(() => {
        DIDWbaAuth.extractAuthHeaderPartsTwoWay(headerWithoutRespDid);
      }).toThrow('Missing required field: resp_did');
    });

    it('should throw error when required fields are missing', () => {
      const incompleteHeader = 'DIDWba did="did:wba:test.example.com", nonce="abc123"';

      expect(() => {
        DIDWbaAuth.extractAuthHeaderPartsTwoWay(incompleteHeader);
      }).toThrow('Missing required field');
    });

    it('should throw error when header does not start with DIDWba', () => {
      const invalidHeader = 'Bearer did="did:wba:test.example.com", resp_did="did:wba:target.example.com", nonce="abc123", timestamp="2024-01-01T00:00:00.000Z", verification_method="key-1", signature="test"';

      expect(() => {
        DIDWbaAuth.extractAuthHeaderPartsTwoWay(invalidHeader);
      }).toThrow('Missing required field');
    });
  });

  describe('verifyAuthHeaderSignatureTwoWay', () => {
    it('should verify valid two-way authentication signature', async () => {
      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';

      const authHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      const result = await DIDWbaAuth.verifyAuthHeaderSignatureTwoWay(
        authHeader,
        testDidDocument,
        serviceDomain
      );

      expect(result.valid).toBe(true);
      expect(result.message).toBe('Signature verification successful');
      expect(result.payload).toBeDefined();
      expect(result.payload?.did).toBe(testDidDocument.id);
      expect(result.payload?.resp_did).toBe(respDid);
      expect(result.payload?.anp_service).toBe(serviceDomain);
    });

    it('should fail verification with wrong service domain', async () => {
      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';
      const wrongServiceDomain = 'wrong.service.com';

      const authHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      const result = await DIDWbaAuth.verifyAuthHeaderSignatureTwoWay(
        authHeader,
        testDidDocument,
        wrongServiceDomain
      );

      expect(result.valid).toBe(false);
      expect(result.message).toBe('Signature verification failed');
    });

    it('should fail verification with tampered signature', async () => {
      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';

      const authHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      // Tamper with the signature
      const tamperedHeader = authHeader.replace(/signature="[^"]+"/g, 'signature="tampered"');

      const result = await DIDWbaAuth.verifyAuthHeaderSignatureTwoWay(
        tamperedHeader,
        testDidDocument,
        serviceDomain
      );

      expect(result.valid).toBe(false);
      expect(result.message).toBe('Signature verification failed');
    });

    it('should fail verification when verification method not found', async () => {
      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';

      const authHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      // Create DID document without verification method
      const didDocumentWithoutVM = {
        ...testDidDocument,
        verificationMethod: []
      };

      const result = await DIDWbaAuth.verifyAuthHeaderSignatureTwoWay(
        authHeader,
        didDocumentWithoutVM,
        serviceDomain
      );

      expect(result.valid).toBe(false);
      expect(result.message).toContain('Verification method not found');
    });
  });

  describe('Two-way vs Single-way Authentication Data Structure', () => {
    it('should use different service field names', async () => {
      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';

      // Generate both types of headers
      const singleWayHeader = await DIDWbaAuth.generateAuthHeader(
        testDidDocument,
        serviceDomain,
        testSignCallback
      );

      const twoWayHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      // Verify single-way uses 'service' field
      const singleWayResult = await DIDWbaAuth.verifyAuthHeaderSignature(
        singleWayHeader,
        testDidDocument,
        serviceDomain
      );

      expect(singleWayResult.valid).toBe(true);
      expect(singleWayResult.payload?.service).toBe(serviceDomain);
      expect(singleWayResult.payload?.anp_service).toBeUndefined();

      // Verify two-way uses 'anp_service' field
      const twoWayResult = await DIDWbaAuth.verifyAuthHeaderSignatureTwoWay(
        twoWayHeader,
        testDidDocument,
        serviceDomain
      );

      expect(twoWayResult.valid).toBe(true);
      expect(twoWayResult.payload?.anp_service).toBe(serviceDomain);
      expect(twoWayResult.payload?.service).toBeUndefined();
    });

    it('should include resp_did only in two-way authentication', async () => {
      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';

      // Single-way should not have resp_did
      const singleWayHeader = await DIDWbaAuth.generateAuthHeader(
        testDidDocument,
        serviceDomain,
        testSignCallback
      );

      expect(singleWayHeader).not.toContain('resp_did=');

      // Two-way should have resp_did
      const twoWayHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      expect(twoWayHeader).toContain(`resp_did="${respDid}"`);
    });
  });

  describe('Error Handling', () => {
    it('should handle malformed auth headers gracefully', async () => {
      const malformedHeaders = [
        'Invalid header format',
        'DIDWba malformed="data"',
        'DIDWba did="test" but missing other fields',
        ''
      ];

      for (const header of malformedHeaders) {
        const result = await DIDWbaAuth.verifyAuthHeaderSignatureTwoWay(
          header,
          testDidDocument,
          'test.service.com'
        );

        expect(result.valid).toBe(false);
        expect(result.message).toContain('error');
      }
    });

    it('should handle verification errors gracefully', async () => {
      const invalidDidDocument = {
        ...testDidDocument,
        verificationMethod: [{
          ...testDidDocument.verificationMethod[0],
          publicKeyJwk: {
            kty: 'EC',
            crv: 'secp256k1',
            x: 'invalid',
            y: 'invalid'
          }
        }]
      } as DIDDocument;

      const respDid = 'did:wba:target.example.com';
      const serviceDomain = 'test.service.com';

      const authHeader = await DIDWbaAuth.generateAuthHeaderTwoWay(
        testDidDocument,
        respDid,
        serviceDomain,
        testSignCallback
      );

      const result = await DIDWbaAuth.verifyAuthHeaderSignatureTwoWay(
        authHeader,
        invalidDidDocument,
        serviceDomain
      );

      expect(result.valid).toBe(false);
      expect(result.message).toContain('error');
    });
  });
});