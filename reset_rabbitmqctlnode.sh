sudo rabbitmqctl stop_app
sudo rabbitmqctl force_reset
sudo rabbitmqctl start_app
sudo rabbitmq-plugins enable rabbitmq_managment
sudo rabbitmqctl add_user admin admin
sudo rabbitmqctl set_user_tags admin administrator
sudo rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"