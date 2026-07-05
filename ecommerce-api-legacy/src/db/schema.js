// Schema + seed de desenvolvimento, isolados da conexão e do entrypoint
// (RP-04 corrige AP-07). A senha do seed é hasheada (RP-03 corrige AP-03).
async function initSchema(db, passwordService) {
    await db.exec(`
        CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
        CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
        CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
        CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
        CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
    `);

    const seedHash = await passwordService.hash('123');
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        'Leonan',
        'leonan@fullcycle.com.br',
        seedHash,
    ]);
    await db.run(
        "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)"
    );
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = initSchema;
