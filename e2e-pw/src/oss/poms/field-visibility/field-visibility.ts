import { expect, Locator, Page } from "src/oss/fixtures";

const ALL_FIELDS_PATH = [
  "uniqueness",
  "predictions",
  "ground_truth",
  "filepath",
  "id",
  "metadata",
  "tags",
];

export class FieldVisibilityPom {
  readonly page: Page;
  readonly assert: FieldVisibilityAsserter;

  readonly sidebar: Locator;
  readonly dialogLocator: Locator;

  constructor(page: Page) {
    this.page = page;
    this.assert = new FieldVisibilityAsserter(this);

    this.sidebar = page.getByTestId("sidebar");
  }

  modalContainer() {
    return this.page.getByTestId("field-visibility-container");
  }

  fieldVisibilityBtn() {
    return this.sidebar.getByTestId("field-visibility-icon");
  }

  async openFieldVisibilityModal() {
    await this.fieldVisibilityBtn().click();
  }

  async hideFields(paths: string[]) {
    await this.openFieldVisibilityModal();

    for (let i = 0; i < paths.length; i++) {
      await this.page
        .getByTestId(`schema-selection-${paths[i]}`)
        .getByRole("checkbox", { checked: true })
        .click();
    }

    await this.submitFieldVisibilityChanges();
  }

  allCheckboxes(fieldPaths: string[], checked: boolean = true) {
    const res = [];
    for (let i = 0; i < fieldPaths.length; i++) {
      res.push(
        this.page
          .getByTestId(`schema-selection-${fieldPaths[i]}`)
          .getByRole("checkbox", { checked })
      );
    }
    return res;
  }

  async submitFieldVisibilityChanges() {
    await this.applyBtn().click();
  }

  async clearFieldVisibilityChanges() {
    await this.clearBtn().click();
  }

  clearBtn() {
    return this.sidebar.getByTestId("field-visibility-btn-clear");
  }

  applyBtn() {
    return this.modalContainer().getByTestId("field-visibility-btn-apply");
  }

  // TODO: replace with sidebar pom coming up
  sidebarField(fieldName: string) {
    return this.sidebar
      .getByTestId(`${fieldName}-field`)
      .locator("div")
      .filter({ hasText: fieldName })
      .nth(1);
  }

  // TODO: move to sidebar pom coming up
  groupField(groupName: string) {
    return this.sidebar.getByTestId(`sidebar-group-${groupName}-field`);
  }
}

class FieldVisibilityAsserter {
  constructor(private readonly svp: FieldVisibilityPom) {}

  async verifyAllFieldsAreSelected() {
    const checkBoxes = this.svp.allCheckboxes(ALL_FIELDS_PATH);
    checkBoxes.forEach(async (checkBox) => {
      await expect(checkBox).toBeChecked();
    });
  }

  async assertModalIsOpen() {
    await expect(this.svp.modalContainer()).toBeVisible();
  }

  async assertFieldInSidebar(fieldName: string) {
    await expect(this.svp.sidebarField(fieldName)).toBeVisible();
  }

  async assertFieldsInSidebar(fieldNames: string[]) {
    for (let i = 0; i < fieldNames.length; i++) {
      await this.assertFieldInSidebar(fieldNames[i]);
    }
  }

  async assertFieldsNotInSidebar(fieldNames: string[]) {
    for (let i = 0; i < fieldNames.length; i++) {
      await this.assertFieldNotInSidebar(fieldNames[i]);
    }
  }

  async assertFieldNotInSidebar(fieldName: string) {
    await expect(this.svp.sidebarField(fieldName)).toBeHidden();
  }

  async assertSidebarGroupIsVisibile(groupName: string) {
    await expect(this.svp.groupField(groupName)).toBeVisible();
  }

  async assertSidebarGroupIsHidden(groupName: string) {
    await expect(this.svp.groupField(groupName)).toBeHidden({ timeout: 1000 });
  }
}
