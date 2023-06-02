 _______________________________________________________________________________
|                                                                               |
|                                   FACOMsg                                     |
|_______________________________________________________________________________|

1. O que é?

 FACOMsg é um sistema de troca de mensagens que utiliza o RabbitMQ para fazer o
 encaminhamento destas mesagens.

2.Funcionamento

  Para que todas as funcionalidades estejam ativas, é necessário que todos os
  servidores estejam ativos, isto é, o servidor de histórico, servidor de perfis,
  além do servidor de banco de dados e o Broker.
  Existe na pasta do projeto está o script run_servers.sh que já executa os servidores
  de histórico e login. É necessário executar ainda o servidor de subscribe e o provedor.

3.Executando o FACOMsg
Estas instruções assumem que o cluster(Broker) já tenha sido criado e configurado.

 3.1.Configurações

    É necessário que sejam configuradas as credenciais de conexão de banco de dados e do broker,
    nos arquivos :

    BROKER
    ConnectionConfig.py

    BD
    HandlerDB.py

 3.2.Rodando o Sistema

    passo0. Inicie o Broker e o Servidor MySQL;
    passo1. Prepare e execute o script run_servers.sh, em um terminal auxiliar, em caso de religamento do Broker, espere uns segundos antes de executar o script;
    passo2. Execute SubscribeServer.py, em um terminal auxiliar;
    passo3. Execute SubscribingProvider.py, em um terminal auxiliar;
    passo4. Execute o programa FACOMsg.py com os parâmetros adequados;

 4. Comandos

    Para o sistema inicial são possíveis os seguintes comandos:

    FACOMsg.py
    FACOMsg.py join
    FACOMsg.py login
    FACOMsg.py login <user> <senha>   // Não recomendado

    Logado no sistema, os comandos disponíveis são:

    send // Comando para enviar uma mensagem
    receive // Para acompanhar em tempo real a chegada de mensagens
    historic // Ver histórico de mensagens enviadas e recebidas
    subscribe // Para solicitar algum serviço de assinatura(por padrão, usuário ou grupo)
    create_group // Para criar um novo grupo
    add_participant // Para adicionar participante em algum grupo criado pelo proprio usuário
    help // Ver opções de comandos
    exit // sair do programa

    OBS.: Dependendo das operações o Ctrl+C pode ter diferentes efeitos,
    podendo encerrar o programa ou esperar por novos comandos.

  5. Exemplos
    sudo ./run_servers.sh
    python FACOMsg.py join
    ...
    python FACOMsg.py login
    ...
