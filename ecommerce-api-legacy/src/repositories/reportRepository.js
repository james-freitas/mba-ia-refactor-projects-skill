class ReportRepository {
    constructor(db) {
        this.db = db;
    }

    // Uma única query com JOINs no lugar do N+1 original (RP-07 corrige AP-06).
    // LEFT JOIN preserva cursos sem matrículas e matrículas sem usuário/pagamento.
    financialRows() {
        return this.db.all(
            `SELECT c.id      AS course_id,
                    c.title   AS course_title,
                    e.id      AS enrollment_id,
                    u.name    AS student_name,
                    p.amount  AS payment_amount,
                    p.status  AS payment_status
             FROM courses c
             LEFT JOIN enrollments e ON e.course_id = c.id
             LEFT JOIN users u       ON u.id = e.user_id
             LEFT JOIN payments p    ON p.enrollment_id = e.id
             ORDER BY c.id, e.id`,
            []
        );
    }
}

module.exports = ReportRepository;
