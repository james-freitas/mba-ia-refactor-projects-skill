const { PAYMENT_STATUS } = require('../utils/constants');

// Monta o relatório financeiro a partir de uma única query (sem N+1).
class ReportService {
    constructor({ reportRepo }) {
        this.reportRepo = reportRepo;
    }

    async financialReport() {
        const rows = await this.reportRepo.financialRows();
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
            }
            const entry = byCourse.get(row.course_id);

            // Curso sem matrículas: mantém revenue 0 e students vazio.
            if (row.enrollment_id == null) continue;

            if (row.payment_status === PAYMENT_STATUS.PAID) {
                entry.revenue += row.payment_amount;
            }
            entry.students.push({
                student: row.student_name || 'Unknown',
                paid: row.payment_amount != null ? row.payment_amount : 0,
            });
        }

        return [...byCourse.values()];
    }
}

module.exports = ReportService;
