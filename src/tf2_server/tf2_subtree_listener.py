import rospy
from tf2_msgs.msg import TFMessage
from tf2_ros import TransformListener, ConnectivityException, Buffer
from tf2_server.srv import RequestTransformStream, RequestTransformStreamRequest, RequestTransformStreamResponse


class TransformSubtreeListener(TransformListener):
    def __init__(self, subtree, buffer, queue_size=None, buff_size=65536, tcp_nodelay=False, max_server_wait=rospy.Duration(-1)):
        assert isinstance(subtree, RequestTransformStreamRequest)
        assert isinstance(buffer, Buffer)

        service_name = rospy.resolve_name("~request_transform_stream", rospy.resolve_name("tf2_server"))
        client = rospy.ServiceProxy(service_name, RequestTransformStream)
        rospy.loginfo("Waiting for service " + service_name, logger_name="tf2_subtree_listener")

        try:
            client.wait_for_service(max_server_wait.to_sec())
        except rospy.ROSException, e:
            raise ConnectivityException(str(e))

        rospy.loginfo("Service " + service_name + " is available now", logger_name="tf2_subtree_listener")

        rospy.loginfo("Requesting topic names for transform subtree", logger_name="tf2_subtree_listener")
        try:
            topics = client.call(subtree)
            assert isinstance(topics, RequestTransformStreamResponse)
        except rospy.ServiceException, e:
            raise ConnectivityException(str(e))

        TransformListener.__init__(self, buffer, queue_size, buff_size, tcp_nodelay)

        self.unregister()
        buffer.clear()

        self.tf_sub = rospy.Subscriber(topics.topic_name, TFMessage, self.callback, queue_size=queue_size, buff_size=buff_size, tcp_nodelay=tcp_nodelay)
        self.tf_static_sub = rospy.Subscriber(topics.static_topic_name, TFMessage, self.static_callback, queue_size=queue_size, buff_size=buff_size, tcp_nodelay=tcp_nodelay)

        rospy.loginfo("Created transform subtree listener with /tf:=%s and /tf_static:=%s" % (
            topics.topic_name, topics.static_topic_name), logger_name="tf2_subtree_listener")

