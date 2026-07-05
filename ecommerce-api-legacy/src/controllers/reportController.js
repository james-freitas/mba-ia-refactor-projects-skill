function reportController(reportService) {
    return async (req, res, next) => {
        try {
            const report = await reportService.financialReport();
            res.json(report);
        } catch (err) {
            next(err);
        }
    };
}

module.exports = reportController;
