### Regras gerais

 - A aplicação deve ser organizada em camadas, separando claramente a lógica de negócios, a lógica de acesso a dados e a lógica de apresentação. Cada camada deve ter responsabilidades bem definidas e não deve depender diretamente de outras camadas.

 - Dados de configuração, como credenciais de banco de dados, URLs de serviços externos e chaves de API, não devem ser hardcoded em scripts ou classes. Eles devem ser armazenados em arquivos de configuração separados ou variáveis de ambiente, garantindo que possam ser facilmente alterados sem modificar o código-fonte.

 - Códigos de conexão, leitura, escrita e exclusão ao banco de dados não deveria ser colocado em scripts, classes ou arquivos que representam a camada de apresentação, como controllers, views ou templates. A lógica de acesso ao banco de dados deve ser encapsulada em classes ou funções específicas para isso, geralmente localizadas em uma camada de repositório.

 - A camada de modelo deve ser responsável apenas por representar os dados e suas relações, sem incluir lógica de negócios complexa. A lógica de negócios deve ser implementada em classes ou funções separadas, geralmente localizadas em uma camada de serviço.

 - A camada de apresentação deve ser responsável apenas por lidar com a interação do usuário e a exibição de informações, sem incluir lógica de negócios ou acesso ao banco de dados. A comunicação entre a camada de apresentação e as camadas de serviço e repositório deve ser feita através de interfaces bem definidas.

 - A camada de serviço deve ser responsável por coordenar a lógica de negócios e orquestrar as operações entre a camada de modelo e a camada de repositório. Ela deve fornecer métodos que encapsulam as regras de negócios e garantem a consistência dos dados.

 - Para cada classe ou função devem haver somente uma única responsabilidade. Isso significa que cada classe ou função deve ter um único propósito e não deve misturar diferentes responsabilidades. Isso facilita a manutenção, o teste e a reutilização do código.

 - Na classe ou script principal, que é responsável por iniciar a aplicação, não deve conter lógica de negócios ou acesso ao banco de dados. Ela deve apenas orquestrar a inicialização das diferentes camadas e componentes da aplicação.

 - Aplicações que contém APIs RESTful devem seguir os princípios de design REST, incluindo o uso adequado de métodos HTTP (GET, POST, PUT, DELETE), códigos de status HTTP apropriados e a utilização de URLs significativas e consistentes para os recursos.

 - Aplicações backend deveriam implementar um health check endpoint, que permite verificar a saúde da aplicação e seus componentes, como banco de dados, serviços externos e dependências. Esse endpoint deve retornar informações sobre o estado da aplicação e permitir que ferramentas de monitoramento possam detectar problemas rapidamente.

- Aplicar o SOLID principles, que são um conjunto de princípios de design orientados a objetos que ajudam a criar código mais modular, flexível e fácil de manter. Esses princípios incluem:

  - **S**: Single Responsibility Principle (Princípio da Responsabilidade Única)
  - **O**: Open/Closed Principle (Princípio Aberto/Fechado)
  - **L**: Liskov Substitution Principle (Princípio da Substituição de Liskov)
  - **I**: Interface Segregation Principle (Princípio da Segregação de Interfaces)
  - **D**: Dependency Inversion Principle (Princípio da Inversão de Dependência)

- Evitar criar classes ou scripts utils ou helpers que contenham métodos estáticos genéricos. Em vez disso, prefira criar classes específicas para cada responsabilidade, promovendo a coesão e facilitando a manutenção do código.

- Classes ou scripts contendo rotas de API não devem conter lógica de negócios ou acesso ao banco de dados. Eles devem apenas mapear as rotas para os métodos apropriados na camada de serviço, garantindo que a lógica de negócios esteja centralizada e seja facilmente testável.