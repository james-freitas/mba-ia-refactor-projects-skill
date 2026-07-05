// Remoção de usuário com cascata transacional — corrige o DELETE que deixava
// matrículas e pagamentos órfãos e respondia sucesso mesmo em erro (AP-09).
class UserService {
    constructor({ db, userRepo, enrollmentRepo, paymentRepo }) {
        this.db = db;
        this.userRepo = userRepo;
        this.enrollmentRepo = enrollmentRepo;
        this.paymentRepo = paymentRepo;
    }

    async deleteUser(id) {
        await this.db.exec('BEGIN');
        try {
            await this.paymentRepo.deleteByUserId(id);
            await this.enrollmentRepo.deleteByUserId(id);
            await this.userRepo.deleteById(id);
            await this.db.exec('COMMIT');
        } catch (err) {
            await this.db.exec('ROLLBACK');
            throw err;
        }
    }
}

module.exports = UserService;
