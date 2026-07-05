class UserRepository {
    constructor(db) {
        this.db = db;
    }

    findByEmail(email) {
        return this.db.get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
    }

    findById(id) {
        return this.db.get('SELECT id, name, email, pass FROM users WHERE id = ?', [id]);
    }

    async create({ name, email, pass }) {
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, pass]
        );
        return lastID;
    }

    deleteById(id) {
        return this.db.run('DELETE FROM users WHERE id = ?', [id]);
    }
}

module.exports = UserRepository;
