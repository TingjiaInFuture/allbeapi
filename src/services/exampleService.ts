export interface ExampleData {
  message: string;
  timestamp: Date;
}

export const getExampleData = (): ExampleData => {
  return {
    message: "这是来自 exampleService 的示例数据",
    timestamp: new Date(),
  };
};
