class CamadaEnlace:
    ignore_checksum = False

    def __init__(self, linhas_seriais):
        """
        Inicia uma camada de enlace com um ou mais enlaces, cada um conectado
        a uma linha serial distinta. O argumento linhas_seriais é um dicionário
        no formato {ip_outra_ponta: linha_serial}. O ip_outra_ponta é o IP do
        host ou roteador que se encontra na outra ponta do enlace, escrito como
        uma string no formato 'x.y.z.w'. A linha_serial é um objeto da classe
        PTY (vide camadafisica.py) ou de outra classe que implemente os métodos
        registrar_recebedor e enviar.
        """
        self.enlaces = {}
        self.callback = None
        # Constrói um Enlace para cada linha serial
        for ip_outra_ponta, linha_serial in linhas_seriais.items():
            enlace = Enlace(linha_serial)
            self.enlaces[ip_outra_ponta] = enlace
            enlace.registrar_recebedor(self._callback)

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de enlace
        """
        self.callback = callback

    def enviar(self, datagrama, next_hop):
        """
        Envia datagrama para next_hop, onde next_hop é um endereço IPv4
        fornecido como string (no formato x.y.z.w). A camada de enlace se
        responsabilizará por encontrar em qual enlace se encontra o next_hop.
        """
        # Encontra o Enlace capaz de alcançar next_hop e envia por ele
        self.enlaces[next_hop].enviar(datagrama)

    def _callback(self, datagrama):
        if self.callback:
            self.callback(datagrama)


class Enlace:
    def __init__(self, linha_serial):
        self.linha_serial = linha_serial
        self.linha_serial.registrar_recebedor(self.__raw_recv)
        self.buffer = b''

    def registrar_recebedor(self, callback):
        self.callback = callback

    def enviar(self, datagrama):
        # TODO: Preencha aqui com o código para enviar o datagrama pela linha
        # serial, fazendo corretamente a delimitação de quadros e o escape de
        # sequências especiais, de acordo com o protocolo CamadaEnlace (RFC 1055).
        self.linha_serial.enviar(b"\xc0" + self.escapar_datagrama(datagrama) + b"\xc0")
        pass

    def __raw_recv(self, dados):
        # TODO: Preencha aqui com o código para receber dados da linha serial.
        # Trate corretamente as sequências de escape. Quando ler um quadro
        # completo, repasse o datagrama contido nesse quadro para a camada
        # superior chamando self.callback. Cuidado pois o argumento dados pode
        # vir quebrado de várias formas diferentes - por exemplo, podem vir
        # apenas pedaços de um quadro, ou um pedaço de quadro seguido de um
        # pedaço de outro, ou vários quadros de uma vez só.

        # Atualizamos os dados com os dados já guardados no buffer
        dados = self.buffer + dados

        # Dividimos possíveis datagramas misturados pelo separados
        dados = dados.split(b'\xc0')

        # Guardamos o resíduo no buffer (último elemento do array)
        self.buffer = dados[-1]

        # Enviamos todos os datagramas completos (menos o último) à camada superior
        for datagrama in dados[:-1]:
            # Não enviamos datagramas vazios
            if datagrama != b"":
                try:
                    self.callback(self.traduzir_datagrama(datagrama))
                except:
                    # Ignoramos exceções
                    import traceback

                    traceback.print_exc()

                finally:
                    # Limpamos possíveis pedaços de datagramas
                    dados = b''


        pass

    def escapar_datagrama(self, datagrama):
        
        # Primeiro escapamos o byte 0xDB que serve para escapar 0xC0
        datagrama_tratado_1 = datagrama.replace(b"\xdb", b"\xdb\xdd")

        # Depois escapamos o byte 0xC0 dentro do datagrama para não haver ambiguidade
        datagrama_tratado_final = datagrama_tratado_1.replace(b"\xc0", b"\xdb\xdc")

        return datagrama_tratado_final
    
    def traduzir_datagrama(self, datagrama):

        # Primeiro extraímos o byte especial 0xC0 escapado
        datagrama_traduzido_1 = datagrama.replace(b"\xdb\xdc", b"\xc0")

        # Depois extraímos o byte 0xDB escapado
        datagrama_traduzido_final = datagrama_traduzido_1.replace(b"\xdb\xdd", b"\xdb")

        return datagrama_traduzido_final




