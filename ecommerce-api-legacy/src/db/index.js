const sqlite3 = require('sqlite3');

// Wrapper de conexão baseado em Promises (RP-10 corrige AP-08: sai o
// `.verbose()` e o estilo callback cru). É a única porta de acesso ao driver;
// os repositories usam estes métodos.
class Database {
    constructor(filename = ':memory:') {
        this.db = new sqlite3.Database(filename);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.run(sql, params, function (err) {
                if (err) return reject(err);
                // `this` traz lastID e changes do statement.
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.db.exec(sql, (err) => (err ? reject(err) : resolve()));
        });
    }
}

module.exports = Database;
