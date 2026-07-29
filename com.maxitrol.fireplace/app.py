from homey.app import App


class MaxitrolFireplaceApp(App):
    async def on_init(self) -> None:
        await super().on_init()
        self.log("Maxitrol app initialized")


homey_export = MaxitrolFireplaceApp
