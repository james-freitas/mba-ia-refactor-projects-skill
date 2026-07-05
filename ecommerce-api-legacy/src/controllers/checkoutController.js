// Controller magro: lê o request, chama o service, mapeia para HTTP (RP-06).
function checkoutController(checkoutService) {
    return async (req, res, next) => {
        const { usr, eml, pwd, c_id, card } = req.body || {};
        if (!usr || !eml || !c_id || !card) return res.status(400).send('Bad Request');

        try {
            const { enrollmentId } = await checkoutService.checkout({
                name: usr,
                email: eml,
                password: pwd,
                courseId: c_id,
                card,
            });
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        } catch (err) {
            next(err);
        }
    };
}

module.exports = checkoutController;
