function userController(userService) {
    return {
        remove: async (req, res, next) => {
            try {
                await userService.deleteUser(req.params.id);
                res.status(200).send('Usuário e dados relacionados removidos');
            } catch (err) {
                next(err);
            }
        },
    };
}

module.exports = userController;
