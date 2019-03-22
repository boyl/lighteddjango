/*

我们需要牢记两点：
①__proto__和constructor属性是对象所独有的；
② prototype属性是函数所独有的，因为函数也是一种对象，所以函数也拥有__proto__和constructor属性。

__proto__属性的作用就是当访问一个对象的属性时，如果该对象内部不存在这个属性，
那么就会去它的__proto__属性所指向的那个对象（父对象）里找，一直找，
直到__proto__属性的终点null，然后返回undefined，通过__proto__属性将对象连接起来的这条链路即我们所谓的原型链。

prototype属性的作用就是让该函数所实例化的对象们都可以找到公用的属性和方法，即f1.__proto__ === Foo.prototype。

constructor属性的含义就是指向该对象的构造函数，所有函数（此时看成对象了）最终的构造函数都指向Function。
---------------------
作者：码飞_CC
来源：CSDN
原文：https://blog.csdn.net/cc18868876837/article/details/81211729
版权声明：本文为博主原创文章，转载请附上博文链接！
 */

(function ($, Backbone, _, app) {
    let Socket = function (server) {
        this.server = server;
        this.ws = null;
        this.connected = new $.Deferred();
        this.open();
    };
    
    Socket.prototype = _.extend(Socket.prototype, Backbone.Events, {
        open: function () {
            if (this.ws === null) {
                this.ws = new WebSocket(this.server);
                this.ws.onopen = $.proxy(this.onopen, this);
                this.ws.onmessage = $.proxy(this.onmessage, this);
                this.ws.onclose = $.proxy(this.onclose, this);
                this.ws.onerror = $.proxy(this.onerror, this);
            }
            return this.connected;
        },

        close: function () {
            if (this.ws && this.ws.close) {
                this.ws.close();
            }
            this.ws = null;
            this.connected = new $.Deferred();
            this.trigger('closed');
        },

        onopen: function () {
            this.connected.resolve();
            this.trigger('open');
        },

        onmessage: function (message) {
            let result = JSON.parse(message.data);
            this.trigger('message', result, message);
            if (result.model && result.action) {
                this.trigger(result.model + ':' + result.action,
                    result.id, result, message);
            }
        },

        onclose: function () {
            this.close();
        },

        onerror: function (error) {
            this.trigger('error', error);
            this.close();
        },

        send: function (message) {
            let self = this,
                payload = JSON.stringify(message);
            this.connected.done(function () {
                self.ws.send(payload);
            });
        }
    });

    app.Socket = Socket;
})(jQuery, Backbone, _, app);