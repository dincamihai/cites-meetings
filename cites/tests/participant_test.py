from common import _BaseTest

class ParticipantTest(_BaseTest):

    def test_send_mail(self):
        from flaskext.mail import Mail
        from flaskext.mail.signals import email_dispatched

        self._create_participant(u"10") # 10: "Member"

        mail = Mail(self.app)
        with mail.record_messages() as outbox:
            resp = self.client.post("/meeting/1/participant/1/send_mail", data=dict(
                to="dragos.catarahia@gmail.com",
                subject="SC61 registration -- Acknowledgment",
                message="Hello world"
            ))

            self.assertEqual(len(outbox), 1)
            self.assertEqual(outbox[0].subject,
                             "SC61 registration -- Acknowledgment")
            self.assertEqual(outbox[0].recipients,
                            ["dragos.catarahia@gmail.com"])
            self.assertEqual(outbox[0].body, u"Hello world")
            self.assertEqual(outbox[0].sender, "meeting@cites.edw.ro")
            self.assertEqual(outbox[0].attachments[0].content_type,
                             "application/pdf")
            self.assertEqual(outbox[0].attachments[0].filename,
                             "credentials.pdf")

    def test_view_pdf(self):
        self._create_participant(u"10") # 10: "Member"

        resp = self.client.get("/meeting/1/participant/1/credentials.pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["Content-Type"], "application/pdf")
