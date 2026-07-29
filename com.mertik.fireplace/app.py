from homey.app import App


class MertikFireplaceApp(App):
    async def on_init(self) -> None:
        await super().on_init()
        self.log("Mertik Fireplace app initialized")


homey_export = MertikFireplaceApp
