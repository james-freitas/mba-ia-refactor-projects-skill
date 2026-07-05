const { scrypt, randomBytes, timingSafeEqual } = require('crypto');
const { promisify } = require('util');
const { DomainError } = require('../utils/errors');

// Hashing forte com salt via scrypt nativo (RP-03 corrige AP-03).
// Substitui o `badCrypto` caseiro; sem dependência nativa extra a compilar.
const scryptAsync = promisify(scrypt);
const KEYLEN = 64;

async function hash(password) {
    if (!password) throw new DomainError('senha obrigatória');
    const salt = randomBytes(16).toString('hex');
    const derived = await scryptAsync(password, salt, KEYLEN);
    return `${salt}:${derived.toString('hex')}`;
}

async function verify(password, stored) {
    if (!password || !stored || !stored.includes(':')) return false;
    const [salt, key] = stored.split(':');
    const keyBuf = Buffer.from(key, 'hex');
    const derived = await scryptAsync(password, salt, KEYLEN);
    return keyBuf.length === derived.length && timingSafeEqual(keyBuf, derived);
}

module.exports = { hash, verify };
